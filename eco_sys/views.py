from eco_sys.utils.utils import ViewUtils
from rank.serializers import RankConfigSerializer, RankSerializer
from .utils import *
from eco_sys import secrets
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from user.models import *
from user.serializers import * 
from category.models import *
from category.serializers import * 
from product.models import *
from product.serializers import *
from coupon.models import *
from coupon.serializers import *
from cart.models import *
from cart.serializers import * 
from view.models import *
from view.serializers import * 
from order.models import *
from order.serializers import * 
from quest.models import *
from quest.serializers import *
from order.tasks import *
from rank.models import *
from rank.serializers import *
from exchange.models import *
from exchange.serializers import *
from subscription.models import *
from subscription.serializers import *

class DebugView(generics.GenericAPIView):
    
    def get(self, request, *args, **kwargs):
        data = {}
        stripe.api_key = secrets.STRIPE_SECRET_KEY
        
        subscription = Subscription.objects.filter(id=4).first()
        for tf in TierFeature.objects.filter(tier=subscription.tier):
            prog = Progress.objects.create(
                subscription=subscription,
                feature=tf.feature,
                isActivated=True,
                progression={}
            )
            data[prog.feature.name] = prog.id
        
        #! test detail Serializer
        # from eco_sys.utils.utils import ViewUtils
        # data = ViewUtils.generic_detail_paginated_response(
        #     self,
        #     request,
        #     Order,
        #     Order.objects.filter(id=request.data['order'])
        # )
        
        #! test apply Benefit
        # order = Order.objects.filter(id=request.data['order']).first()
        # order.refresh_from_db()
        # shop = order.orderitem_set.first().product.shop
        # user = order.user
        # user_benefits = [UserBenefitSerializer(item).data for item in UserBenefit.objects.filter(shop=shop, user=user, is_activate=True)]
        # data['benefits'] = user_benefits
        # data['final charge -before'] = order.final_charge
        # data['total charge -before'] = order.total_charge

        # for benefit in user_benefits:
        #     if benefit['benefit_type'] == 'percentage':
        #         order.final_charge = float(order.final_charge) * (1 - benefit['benefit'])
        # for benefit in user_benefits:
        #     if benefit['benefit_type'] == 'direct':
        #         order.final_charge = float(order.final_charge) - benefit['benefit']
        # order.final_charge = 0 if order.final_charge < 0 else order.final_charge
        # data['final charge -after'] = order.final_charge
        # data['total charge -after'] = order.total_charge
        
        #! test quest_finder
        # user = User.objects.filter(id=request.data['user']).first()
        # order = Order.objects.filter(id=request.data['order']).first()
        # shop = order.orderitem_set.all()[0].product.shop
        # buyer = user.buyer_set.filter(shop=shop).first()
        # orderitem = order.orderitem_set.all()[0]
        # data['quest found'] = QuestSerializer(quest_finder(shop, buyer, orderitem)).data
        # data['all quest'] = QuestSerializer(Quest.objects.filter(shop=shop), many=True).data
        # data['point gain'] = PointGainSerializer(PointGain.objects.filter(buyer=buyer), many=True).data
        
        #! test Rank up, receive Benefits and apply Benefits
        # order = Order.objects.filter(id=request.data['order']).first()
        # data['order'] = OrderSerializer(order).data
        # user = order.user
        # orderitems = order.orderitem_set.all()
        # shop = orderitems[0].product.shop
        # if not shop: return
        
        # buyer, cur_rank = get_or_create_buyer(user, shop)
        # data['buyer'] = BuyerSerializer(buyer).data
        # data['current-rank'] = RankConfigSerializer(cur_rank).data
        
        # # apply_benefit(order)
        # for orderitem in orderitems: 
        #     quest = quest_finder(shop, buyer, orderitem)
        #     if not quest: 
        #         print ('No Quest found')
        #         continue
        #     pointgain = get_or_create_pointgain(buyer, cur_rank, quest)
        #     pointgain.insert_orderitem(orderitem.id)
        #     update_progress(shop, buyer, cur_rank, quest, pointgain,orderitem)
        # data['user-benefits'] = UserBenefitSerializer(user.userbenefit_set, many=True).data
        # data['gain-point'] = PointGainSerializer(buyer.pointgain_set, many=True).data
        # data['order -later'] = OrderSerializer(order).data
        # data['buyer -later'] = BuyerSerializer(buyer).data
        
        return Response(data, status=HTTP_200_OK)
        data = [field.name for field in buyer._meta.get_fields()]
        
        #! make changes to Rank and RankConfig
        # updates = {
        #     'Guest' : [],
        #     'Emerald': [8,4] ,
        #     'Gold': [7,3],
        #     'Silver': [7,4] ,
        #     'Bronze': [5,6] ,
        #     'Iron': [5]
        #     }
        # updates_ = [RankSerializer(item, data={'benefits':updates[item.name]}, partial=True) for item in Rank.objects.all()]
        # updates_ = [item.save() for item in updates_ if item.is_valid()]
        # data=RankSerializer(updates_, many=True).data
        # return Response(data, status=HTTP_200_OK)
        
        #! test update Quest progress
        # if request.data['user_id']==0: user = request.user
        # else: user = User.objects.filter(id=request.data['user_id']).first()
        # order = Order.objects.filter(id=request.data['order_id']).first()
        # orderitems = order.orderitem_set.all()
        # shop = orderitems[0].product.shop
        # data={}
        # for orderitem in orderitems:
        #     buyer, cur_rank = get_or_create_buyer(user, shop)
        #     data.update({
        #         'found buyer': BuyerSerializer(buyer).data,
        #         'found cur_rank': RankConfigSerializer(cur_rank).data
        #     })
        #     quest = quest_finder(shop, buyer, orderitem)
        #     data.update({'found quest': QuestSerializer(quest).data})
        #     if not quest: return Response(data, status=HTTP_200_OK)
        #     pointgain = get_or_create_pointgain(buyer, cur_rank, quest)
        #     # print ('view', [field.name for field in order._meta.get_fields()])
        #     # print ('view', [item.product.id for item in order.orderitem_set.all()])
        #     data.update({'found pointgain': PointGainSerializer(pointgain).data})
        #     update_progress(shop, buyer, cur_rank, quest, pointgain, orderitem)
        #     data.update({'updated pointgain': PointGainSerializer(pointgain).data})
        # return Response(data, status=HTTP_200_OK)
        
        #! change product 1-99 to shop Countryfood
        # seri_ = []
        # for i in range(1,100):
        #     prod = Product.objects.filter(id=i).first()
        #     prod_seri = ProductSerializer(prod, data={'shop':14}, partial=True)
        #     if not prod_seri.is_valid():
        #         data = ViewUtils.gen_response(data=prod_seri.errors)
        #         return Response(data, data['status'])
        #     seri_.append(prod_seri)
        # try:
        #     [seri.save() for seri in seri_]
        # except Exception as e:
        #     data = ViewUtils.gen_response(data=str(e))
        #     return Response(data, data['status'])
        # data = ViewUtils.gen_response(success=True,status=HTTP_200_OK,message='Change succeed!',data=f'{len(seri_)} products changed')
        # return Response(data, data['status'])
        
        # obj = Order.objects.filter(user=request.user)
        # evryth = Order.everything.filter(user=request.user)
        
        # data_ = {
        #     'order': OrderSerializer(obj, many=True).data,
        #     'everything': OrderSerializer(evryth, many=True).data
        # }
        # data = ViewUtils.paginated_get_response(
        #     self,
        #     request,
        #     OrderSerializer,
        #     evryth
        #     )
        # return Response(data, data['status'])
        
        #! Test restore
        # content = {}
        # items = CartItem.deleted
        # [item.restore() for item in items]
        # serializer_restored = CartItemSerializer(CartItem.objects.all(), many=True)
        # content['restored'] = serializer_restored.data
        # [item.delete() for item in items]
        # serializer_deleted = CartItemSerializer(CartItem.objects.all(), many=True)
        # content['deleted'] = serializer_deleted.data
        # return Response(content, status=HTTP_200_OK)
        
        #! Test ordering manually made
        #@ If using Django ORM
        # ordered_values = OrderItem.objects.values('product').annotate(count=Count('product')).order_by('-count')
        # serializer = ProductSerializer(Product.objects.filter(id__in=[item['product'] for item in ordered_values]), many=True)
        
        # content = {
        #     'message': 'Debugging',
        #     'rawdata of %d items' % (len(ordered_values)): [
        #         {
        #             'times ordered': item.get('count'),
        #             'product': data
        #             }
        #                 for item, data in zip(ordered_values, serializer.data)]
        # }
        
        # #@ If using raw SQL
        # raw_sql = """
        #     SELECT order_orderitem.id, order_orderitem.product_id, COUNT(order_orderitem.product_id) as num_views
        #     FROM order_orderitem
        #     GROUP BY order_orderitem.product_id
        #     ORDER BY num_views DESC;
        # """
        # ordered_orderitems = OrderItem.objects.raw(raw_sql)
        
        # content = {
        #     'message': 'Debugging',
        #     'rawdata of %d items' % (len(ordered_orderitems)): [
        #         {
        #             'times ordered': item.num_views,
        #             'product': ProductSerializer(item.product).data
        #             }
        #                 for item in ordered_orderitems]
        # }
        