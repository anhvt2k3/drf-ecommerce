import threading

from django.db.models import Q, F
from django.db import transaction
from django.utils import timezone

from benefit.models import ConfigBenefit, UserBenefit
from benefit.serializers import UserBenefitSerializer
from exchange.models import PointExchange
from order.models import Order
from promotion.models import Promotion
from quest.models import Quest
from shop.models import Buyer, PointGain, Progress
from shop.serializers import BuyerSerializer, PointGainSerializer, ProgressSerializer

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
        
                        ##################################
                        ##          COMPONENTS          ##
                        ##################################

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
        UserBenefit.objects.filter(user=buyer.user, shop=shop, benefit__rank_required=cur_rank).update(is_activate=False)
        # seri_ = [UserBenefitSerializer(item, data={'is_activate':False}, partial=True) for item in UserBenefit.objects.filter(user=buyer.user, shop=shop, benefit__rank_required=cur_rank)]
        # [seri.save() for seri in seri_ if seri.is_valid(raise_exception=True)]
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
        if not order.flashsale:
            promo = get_promo(user, order=order) 
        else:
            promo = None
            order.store_benefit({'source':f'Flashsale[{order.flashsale.id}]'})
        benefits = retrieve_discounts(user,shop,coupon=coupon,order=order,promo=promo)
        
        #! log benefits
        if promo: order.promotion = promo
        if coupon: PointExchange.objects.filter(buyer__user=user,coupon=coupon.id).update(remain_usage=F('remain_usage')-1)
        order.final_charge = apply_discounts(benefits,float(order.total_charge),order=order)
        order.save()
        
                        ##################################
                        ##          COMPONENTS          ##
                        ##################################
                        
def apply_discounts(benefits, total_charge, **kwargs):
    order = kwargs.get('order')
    for benefit in benefits:
        benefitType = benefit.pop('benefit_type')
        benefitValue = benefit.pop('benefit')
        if benefitType == 'percentage':
            total_charge = total_charge * (1 - float(benefitValue))
        elif benefitType == 'direct':
            total_charge = total_charge - float(benefitValue)
        total_charge = 5 if total_charge < 5 else total_charge
        if order: order.store_benefit(benefit)
    return total_charge

def retrieve_discounts(user,shop,**kwargs):
    #! benefit comes from
    benefits = [{
                    'config_benefit': item.benefit,
                    'source': f'RankConfig[{item.benefit.rank_required.id}]',
                    'benefit_type':item.benefit.default_benefit.benefit_type,
                    'benefit':item.benefit.config_amount 
                }
            for item in UserBenefit.objects.filter(shop=shop, user=user, is_activate=True).order_by('-benefit__default_benefit__benefit_type')]
    #! benefit comes from promotion
    if (promos := kwargs.get('promo')):
        benefits += [{
                        # 'config_benefit': 0,
                        'source': f'Promotion[{item.id}]',
                        'benefit_type': item.benefit_type,
                        'benefit':item.benefit_value 
                    }
            for item in [promos]] if promos else []
    #! benefit comes from coupon
    if (coupon := kwargs.get('coupon')):
        benefits += [{  
                        'config_benefit': item,
                        'source': f'Coupon[{coupon.id}]',
                        'benefit_type':item.default_benefit.benefit_type,
                        'benefit':item.config_amount 
                    } 
            for item in coupon.benefit_set.all().order_by('-default_benefit__benefit_type')] if coupon else []
    return benefits

def get_promo(user, **kwargs) -> Promotion:
#* tuple(shop=list[<shop>], items=list[<temp_orderitem>])
    if (order := kwargs.get('order')):
        shop = order.orderitem_set.first().product.shop
        items = [{
                        'product': item.product,
                        'quantity': item.quantity,
                        'price': item.product.price,
                        'charge': item.total_charge
                    }
                for item in order.orderitem_set.all()]
        # print (f'Items {items}')
    elif (cart := kwargs.get('cart')):
        shop, items = cart
    else:
        return []
    # get promo used
    unconditioned_promos = Promotion.objects.filter(shop=shop,start_date__lte=timezone.now(),end_date__gte=timezone.now()).order_by('-priority')
    # get promo conditioned and have higher priority
    conditioned_promos = [promo for promo in unconditioned_promos 
        if promocond_check(promo, items, user) and promo.priority == unconditioned_promos[0].priority]
    return conditioned_promos[0] if conditioned_promos else None
    
def promocond_check(promo, items, user):
    conditions = promo.promocondition_set.all()
    for condition in conditions:
        if condition.cond_type == 'product_range':
            if not set(condition.cond_choice).issubset(set([item['product'].id for item in items])):
                return False
        elif condition.cond_type == 'applies':
            if promo.order_set.filter(user=user).count() >= condition.cond_max:
                return False
        elif condition.cond_type == 'charge':
            # print (f'Charge {sum([item["charge"] for item in items])} < {condition.cond_min}')
            if sum([item['charge'] for item in items]) < condition.cond_min:
                return False
        elif condition.cond_type == 'quantity':
            if sum([item['quantity'] for item in items]) < condition.cond_min:
                return False
        elif condition.cond_type == 'rank':
            if not user.buyer.rank.name in condition.cond_choice:
                return False
        elif condition.cond_type == 'item_charge':
            if any([item['charge'] < condition.cond_min for item in items]):
                return False
        elif condition.cond_type == 'item_quantity':
            if any([item['quantity'] < condition.cond_min for item in items]):
                return False
    return True