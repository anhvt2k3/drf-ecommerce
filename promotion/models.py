from django.db import models
from django.utils import timezone
from datetime import timedelta
from eco_sys.mixins import SoftDeleteModelMixin

# Create your models here.
class DefaultPromotion(SoftDeleteModelMixin, models.Model):
    name = models.CharField(max_length=200)
    benefit_type = models.CharField(max_length=200)
    benefit_value = models.FloatField(default=0)
    
    description = models.TextField(default="A Sale program created by Admin for all Shop to utilize.")

class Promotion(SoftDeleteModelMixin, models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now() + timedelta(days=1))
    benefit_type = models.CharField(max_length=200)
    benefit_value = models.TextField(default=0) #@ containing problem can be fixed by split(',') before using
    
    description = models.TextField(default="A Sale program created by Shop to attain Buyers.")


class PromoCondition(SoftDeleteModelMixin, models.Model):
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, blank=True, null=True)
    defaultPromo = models.ForeignKey(DefaultPromotion, on_delete=models.CASCADE, blank=True, null=True)
    
    cond_type = models.CharField(max_length=200)
    cond_choice = models.JSONField(default=list) ## usecase: 'product_range'=[1,2,3,4,5]
    cond_min = models.FloatField(default=0)
    """
        cond_type = 'product_range' -> cond_choices = [1,2,3,4,5]
        cond_type = 'charge' -> cond_min = 70.25 ## apply to whole order
        cond_type = 'quantity' -> cond_min = 1
        cond_type = 'rank' -> cond_choices = ['Bronze', 'Silver', 'Gold', 'Platinum']
        cond_type = 'item_charge' -> cond_min = 10 ## apply to each item
        cond_type = 'item_quantity' -> cond_min = 1
    """
    
    description = models.TextField(default="A condition that must be met for the Promotion to be applied.")