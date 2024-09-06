from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin

# Create your models here.
class Flashsale(SoftDeleteModelMixin, models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    description = models.TextField(default="A Flashsale that is created by Shop that consists of many Flashsale Products.")
    
class FlashsaleLimit(SoftDeleteModelMixin, models.Model):
    type = models.CharField(max_length=200)
    value = models.TextField()
    unit = models.CharField(max_length=200)
    
class FlashsaleProduct(SoftDeleteModelMixin, models.Model):
    flashsale = models.ForeignKey(Flashsale, on_delete=models.CASCADE)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    stock = models.IntegerField(default=0)
    sale_price = models.FloatField(default=0)
    sale_limit = models.IntegerField(default=0) # limit quantity per buyer
    
class FlashsaleCondition(SoftDeleteModelMixin, models.Model):
    flashsale = models.ForeignKey(Flashsale, on_delete=models.CASCADE)
    type = models.CharField(max_length=200)
    min = models.FloatField(default=0)
    max = models.FloatField(default=0)
    choice = models.JSONField(default=list, blank=True, null=True)
    
