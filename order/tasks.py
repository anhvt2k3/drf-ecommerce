import threading

from django.db.models import Q
from django.db import transaction
from django.utils import timezone

from benefit.models import ConfigBenefit, UserBenefit
from benefit.serializers import UserBenefitSerializer
from coupon.models import Coupon
from exchange.models import PointExchange
from order.models import Order
from quest.models import Quest
from quest.serializers import QuestSerializer
from shop.models import Buyer, PointGain, Progress
from shop.serializers import BuyerSerializer, PointGainSerializer, ProgressSerializer
from user.models import User

loyalty_lock = threading.Lock()
def loyalty_logics(order : Order):
    user = order.user
    orderitems = order.orderitem_set.all()
    shop = orderitems[0].product.shop
    if not shop: return
    with loyalty_lock:
        buyer, cur_rank = get_or_create_buyer(user, shop)
        for orderitem in orderitems:
            quest = quest_finder(shop, buyer, orderitem)
            if not quest: 
                print ('No Quest found')
                continue
            pointgain = get_or_create_pointgain(buyer, cur_rank, quest)
            pointgain.insert_orderitem(orderitem.id)
            cur_rank = update_progress(shop, buyer, cur_rank, quest, pointgain,orderitem)

def get_or_create_buyer(user, shop):
    buyer = Buyer.objects.filter(user=user, shop=shop).first()
    if not buyer:
        seri = BuyerSerializer(data={'user': user.id, 'shop': shop.id})
        seri.is_valid(raise_exception=True)
        buyer = seri.save()
    return buyer, buyer.rank

def quest_finder(shop, buyer, orderitem):
    #? might have to use transactions to lock Quests
    quest_filter =  Q(shop=shop) & Q(product_range__contains=[orderitem.product.id]) & (Q(end_date__gte=timezone.now()) | Q(end_date__isnull=True)) 
    # print ("Quest filter", Quest.objects.filter(product_range__contains=[orderitem.product.id]))
    quests = Quest.objects.filter(quest_filter)
    quests_with_progress = quests.filter(pointgain__buyer=buyer)
    # print ("Quests with progress ", quests_with_progress)
    quests_with_progress_ = quests.filter(pointgain__buyer=buyer, pointgain__gain_point=0)
    # print ("Quests with progress _", quests_with_progress_)
    quests_without_progress = quests.exclude(id__in=quests_with_progress.values_list('id', flat=True))
    # print ("Quests without progress", quests_without_progress)
    ordered_quests = (quests_with_progress_.union(quests_without_progress)).order_by('-reward_point')
    # print ("Quests", ordered_quests)
    quest = ordered_quests.first()
    
    return quest

def get_or_create_pointgain(buyer, cur_rank, quest):
    pointgain = PointGain.objects.filter(buyer=buyer, quest=quest, gain_point=0).first()
    if not pointgain:
        seri = PointGainSerializer(data={'buyer': buyer.id, 'quest': quest.id, 'current_rank': cur_rank.rank.name})
        seri.is_valid(raise_exception=True)
        pointgain = seri.save()
    return pointgain

def update_progress(shop, buyer, cur_rank, quest, pointgain,
orderitem):
    #! update progress
    progress_quantity = pointgain.progress_set.filter(prog_type='quantity').first()
    seri = ProgressSerializer(progress_quantity, data={'progression': progress_quantity.progression+orderitem.quantity}, partial=True)
    seri.is_valid(raise_exception=True)
    seri.save()
    
    progress_spending = pointgain.progress_set.filter(prog_type='spending').first()
    seri = ProgressSerializer(progress_spending, data={'progression': progress_spending.progression+float(orderitem.total_charge)}, partial=True)
    seri.is_valid(raise_exception=True)
    seri.save()
    #! check if completed
    quantity_check = progress_quantity.progression >= quest.min_quantity
    spending_check = progress_spending.progression >= quest.min_spent
    if quantity_check and spending_check:
        pointgain.gain_point = quest.reward_point
        buyer.total_point += pointgain.gain_point
        pointgain.save()
        return updateRank(shop, buyer, cur_rank)
    return cur_rank

def updateRank(shop, buyer, cur_rank):
    rankcfg = shop.rankconfig_set.filter(required_point__lte=buyer.total_point).order_by('-required_point').first()
    # print (f'Rank Config {rankcfg.id}, name: {rankcfg.rank.name}')
    # print (f'current Rank Config {cur_rank.id}, name: {cur_rank.rank.name}')
    if rankcfg and rankcfg.id != cur_rank.id:
        buyer.rank = rankcfg
        ## deactivate old benefits
        seri_ = [UserBenefitSerializer(item, data={'is_activate':False}, partial=True) for item in UserBenefit.objects.filter(user=buyer.user, shop=shop, benefit__rank_required=cur_rank)]
        [seri.save() for seri in seri_ if seri.is_valid(raise_exception=True)]
        cur_rank = rankcfg
        ## create new benefits
        benefits = ConfigBenefit.objects.filter(rank_required=rankcfg)
        for benefit in benefits:
            serializer = UserBenefitSerializer(data={'benefit': benefit.id, 'shop': shop.id, 'user': buyer.user.id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
    buyer.save()
    return cur_rank
    

    
# benefit_lock = threading.Lock()
def apply_benefit(order_id):
    # with benefit_lock:
    with transaction.atomic():
        order = Order.objects.select_for_update().get(id=order_id)
        coupon = order.coupon
        shop = order.orderitem_set.first().product.shop
        user = order.user
        benefits = []
        benefits += [{
                        'config_benefit': item.benefit,
                        'source': f'RankConfig[{item.benefit.rank_required.id}]',
                        'benefit_type':item.benefit.default_benefit.discount_type,
                        'benefit':item.benefit.config_amount 
                        }  
            for item in UserBenefit.objects.filter(shop=shop, user=user, is_activate=True).order_by('-benefit__default_benefit__discount_type')]
        benefits += [{  
                        'config_benefit': item,
                        'source': f'Coupon[{coupon.id}]',
                        'benefit_type':item.default_benefit.discount_type,
                        'benefit':item.config_amount 
                        } 
            for item in coupon.benefit_set.all().order_by('-default_benefit__discount_type')] if coupon else []
        # print ('total charge -before', order.total_charge)
        # print ('final charge -before', order.final_charge)
        current_total = float(order.total_charge)
        for benefit in benefits:
            benefitType = benefit.pop('benefit_type')
            benefitValue = benefit.pop('benefit')
            if benefitType == 'percentage':
                current_total = current_total * (1 - benefitValue)
            elif benefitType == 'direct':
                current_total = current_total - benefitValue
            current_total = 0 if current_total < 0 else current_total
            order.store_benefit(benefit)
            
        order.final_charge = current_total
        order.save()
                
        # print ('total charge -after', order.total_charge)
        # print ('final charge -after', order.final_charge)
