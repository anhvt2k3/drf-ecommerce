from typing import Any
from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin, SoftDeleteManager
from category.models import Category

# Create your models here.
class PointExchangeManager(SoftDeleteManager):
    def used_point(self, buyer):
        return self.filter(buyer=buyer).aggregate(point_sum=models.Sum('coupon__exchange_point'))['point_sum'] or 0

class PointExchange(SoftDeleteModelMixin, models.Model):
    buyer = models.ForeignKey('shop.Buyer', on_delete=models.CASCADE)
    coupon = models.ForeignKey('coupon.Coupon', on_delete=models.CASCADE)
    remain_usage = models.IntegerField(default=0)
    
    description = models.TextField(default="Recording the history of User exchanging Points for Coupons.")
    
    objects = PointExchangeManager()
    
    def __str__(self):
        return f"Exchanged Coupon[{self.coupon.id}]_{self.coupon.exchange_point}pts_{self.remain_usage}"