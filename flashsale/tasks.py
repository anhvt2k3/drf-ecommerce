from datetime import timedelta
from .models import *
from order.models import Order, OrderItem
from .serializers import *
from shop.models import Buyer
from django.db import models

def calculations_N_apply_flashsale(flashsale, items: list, user, is_order=False):
    if flashsale:
        # reconcileWTime(flashsale)
        reconcileWCondition(flashsale.flashsalecondition_set.all(), user, items)
    total_charge = 0
    for item in items:
        if (fproduct := FlashsaleProduct.objects.filter(flashsale=flashsale, product=item['product']).first()):
            reconcileWFProduct(flashsale, user, item, fproduct)
            
            item['price'] = fproduct.sale_price
        if is_order:
            item['total_charge'] = item['price'] * item['quantity']
            item['product'].in_stock = item['product'].in_stock - item['quantity']
            item['product'].save()
        else:
            item['charge'] = item['price'] * item['quantity']
            
        total_charge += item['charge'] if not is_order else item['total_charge']
    return items, total_charge


###############################################

def reconcileWFProduct(flashsale, user, item, fproduct):
    #! Check if product has available stock
    fproduct_sold_quantity = OrderItem.objects.filter(order__flashsale=flashsale).exclude(price=models.F('product__price')).aggregate(fsolds=models.Sum(models.F('quantity')))['fsolds'] or 0
    if fproduct.stock - fproduct_sold_quantity < item['quantity']:
        raise serializers.ValidationError('Flashsale is over for product: ' + item['product'].name)
    #! Check if user is ordering over the sale limit
    fproduct_user_bought = OrderItem.objects.filter(order__flashsale=flashsale,order__user=user, product=item['product']).aggregate(solds=models.Sum('quantity'))['solds'] or 0
    bought_and_intended = fproduct_user_bought + item['quantity']
    if bought_and_intended >= fproduct.sale_limit:
        raise serializers.ValidationError('User is exceeding the sale limit one is allowed to order!')
    
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
            if Order.objects.filter(user=user, flashsale=cond.flashsale).count() >= cond.max:
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



###############################################

def reconcileWLimit(flashsale, products):
    prod_limit = FlashsaleLimit.objects.all()
    for limit in prod_limit:
        if limit.type == 'product:max-flashsale' and products:
            limitation = int(limit.value)
            for product in products:
                if FlashsaleProduct.objects.filter(product=product['product']).count() >= limitation:
                    raise serializers.ValidationError('Product has joined too many Flash sales. Max Flash sales to join is ' + str(limitation))
        elif limit.type == 'sale:max-period':
            limitation = {f'{limit.unit}': limit.value}
            if (flashsale['end_date'] - flashsale['start_date']) > timedelta(**limitation):
                raise serializers.ValidationError('Flashsale period is too long! Max period is ' + str(limitation))