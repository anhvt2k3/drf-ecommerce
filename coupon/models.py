from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin

# Create your models here.
class DefaultCoupon(SoftDeleteModelMixin, models.Model):
    benefit_set = models.ManyToManyField('benefit.DefaultBenefit')
    exchange_point = models.IntegerField(default=0)
    usage_limit = models.IntegerField(default=1)
    
    description = models.TextField(default="A Default Coupon in the Ecommerce System to help Admin create defaults Coupon for Merchants to reuse.")
    
    def __str__(self):
        return f"DefaultCoupon[{self.id}]_{self.exchange_point}pts"
    
class Coupon(SoftDeleteModelMixin, models.Model):
    default = models.ForeignKey(DefaultCoupon, on_delete=models.CASCADE)
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    benefit_set = models.ManyToManyField('benefit.ConfigBenefit')
    exchange_point = models.IntegerField(default=0)
    usage_limit = models.IntegerField(default=1)
    
    description = models.TextField(default="A Coupon in the Ecommerce System to help Admin create sale campaigns to draw in more User.")
    
    def __str__(self):
        return f"Coupon[{self.id}]_{self.shop.name}(remain: {self.usage_limit})"