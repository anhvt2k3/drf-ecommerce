from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin
from user.models import User
from coupon.models import Coupon
from product.models import Product

# Create your models here.
ORDER_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('paid', 'Paid'),
    ('refunded', 'Refunded'),
    ('paidout', 'Paidout'),
    ('cancelled', 'Cancelled'),
]

class Order(SoftDeleteModelMixin, models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    promotion = models.ForeignKey('promotion.Promotion', on_delete=models.SET_NULL, null=True, blank=True)
    flashsale = models.ForeignKey('flashsale.FlashSale', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default='pending')
    total_charge = models.FloatField(default=0.00) #@ charges that is changed by Order Items
    final_charge = models.FloatField(default=0.00) #@ charges that is changed by Discount

    receipt = models.JSONField(default=dict) ## payment intent response object
    refundd = models.JSONField(default=dict) ## refund response object
    
    description = models.TextField(default="An Order which is created by User that consists of many Order Items.")
    
    @property
    def shop(self):
        product_shop = self.orderitem_set.first().product.shop if self.orderitem_set.exists() else None
        coupon_shop = self.coupon.shop if self.coupon else None
        promotion_shop = self.promotion.shop if self.promotion else None
        return product_shop or coupon_shop or promotion_shop
    
    @property
    def benefits(self):
        return [str(item) for item in self.orderbenefit_set.all()]
    
    def reset_total_charge(self):
        total_charge = OrderItem.objects.filter(order=self).aggregate(
            total=models.Sum(models.F('price') * models.F('quantity'))
        )['total'] or 0
        self.total_charge = total_charge
        self.save()
    
    def store_benefit(self, benefit):
        # create new OrderBenefit without identical source
        if 'config_benefit' in benefit and not OrderBenefit.objects.filter(order=self, source=benefit['source'], config_benefit=benefit['config_benefit']).exists():
            OrderBenefit.objects.create(order=self, **benefit)
        elif not OrderBenefit.objects.filter(order=self, source=benefit['source']).exists():
            OrderBenefit.objects.create(order=self, **benefit)
            
    
    
class OrderItem(SoftDeleteModelMixin, models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING)
    quantity = models.IntegerField()
    price = models.FloatField(default=0.00)
    total_charge = models.FloatField(default=0.00)
    
    description = models.TextField(default="An Order Item which is created by User that linked to a Product.")
    
    def reset_total_charge(self):
        self.total_charge = self.price * self.quantity
        self.save()
    
    
class OrderBenefit(SoftDeleteModelMixin, models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    config_benefit = models.ForeignKey('benefit.ConfigBenefit', on_delete=models.DO_NOTHING, blank=True, null=True)
    #* source of the given benefit (can be from coupon or rank)
    #* format: "Coupon[<id>]" or "Rank[<id>]"
    source = models.TextField()
    
    def __str__(self):
        return f"{self.source}"