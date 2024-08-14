from .models import *
from order.models import Order, OrderItem
from serializers import *
from shop.models import Buyer
from django.db import models

def apply_flashsale(flashsale, items: list, user):
    if not reconcileWTime(flashsale): return
    if not reconcileWCondition(flashsale.flashsalecondition_set.all(), user, items): return
    for item in items:
        if (fproduct := FlashsaleProduct.objects.filter(flashsale=flashsale, product=item['product']).first()):
            #! Check if this user has bought enough of this product
            fproduct_user_bought = OrderItem.objects.filter(order__user=user, product=item['product']).aggregate(solds=models.Sum('quantity'))['solds'] or 0
            if fproduct_user_bought >= fproduct.sale_limit:
                raise serializers.ValidationError('User has already bought the maximum quantity of this product!')
            #! Check if product has available stock
            fproduct_sold_quantity = OrderItem.objects.exclude(price=models.F('product__price')).aggregate(fsolds=models.Sum(models.F('quantity')))['fsolds'] or 0
            if fproduct.stock - fproduct_sold_quantity < item['quantity']:
                raise serializers.ValidationError('Flashsale is over for product: ' + item['product'].name)
            
            item['price'] = fproduct.sale_price
    return items
        
        
        
        
    
def reconcileWTime(flashsale):
    from django.utils import timezone
    
    if flashsale.start_date > timezone.now():
        raise serializers.ValidationError('Flashsale has not started yet!')
    if flashsale.end_date < timezone.now():
        raise serializers.ValidationError('Flashsale has ended!')
    return True
    
def reconcileWCondition(conditions,user,items):
    for cond in conditions:
        if cond.type == 'applies':
            if Order.objects.filter(user=user, flashsale=cond.flashsale) >= cond.max:
                raise serializers.ValidationError('Buyer have already applied this flashsale too many times!')
        elif cond.type == 'rank':
            if not Buyer.objects.filter(user=user,shop=cond.flashsale.shop,rank__rank__name__in=cond.choice).exists():
                raise serializers.ValidationError('Buyer does not have the required rank!')
        elif cond.type == 'max-users':
            if cond.flashsale.order_set.values('user').distinct().count() >= cond.max:
                raise serializers.ValidationError('Flashsale has reached the maximum number of users!')
        elif cond.type == 'max-orders':
            if cond.flashsale.order_set.count() >= cond.max:
                raise serializers.ValidationError('Flashsale has reached the maximum number of orders!')
    return True