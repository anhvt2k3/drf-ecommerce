from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin

# Create your models here.
class Promotion(SoftDeleteModelMixin, models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    default_benefit = models.ForeignKey('benefit.DefaultBenefit', on_delete=models.CASCADE)
    benefit_type = models.CharField(max_length=200)
    benefit_value = models.FloatField(default=0)
    
    description = models.TextField(default="A Sale program created by Shop to attain Buyers.")
    
class PromoCondition(SoftDeleteModelMixin, models.Model):
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE)
    cond_type = models.CharField(max_length=200)
    cond_choice = models.JSONField(default=list) ## usecase: 'product_range'=[1,2,3,4,5]
    cond_min = models.FloatField(default=0)
    """
        cond_type = 'product_range' -> cond_choices = [1,2,3,4,5]
        cond_type = 'charge' -> cond_min = 100
        cond_type = 'quantity' -> cond_min = 1
        cond_type = 'rank' -> cond_choices = ['Bronze', 'Silver', 'Gold', 'Platinum']
        cond_type = 'item_charge' -> cond_min = 10
        cond_type = 'item_quantity' -> cond_min = 1
    """
    
    description = models.TextField(default="A condition that must be met for the Promotion to be applied.")