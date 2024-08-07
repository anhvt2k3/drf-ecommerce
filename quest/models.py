from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin

# Create your models here.
class Quest(SoftDeleteModelMixin, models.Model):
    #todo Add field to limit the number of times a quest can be completed.
    #todo Add field to limit participatnts based on Buyer rank.
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    reward_point = models.IntegerField(default=0)
    product_range = models.JSONField(default=list) 
    min_spent = models.FloatField(default=0)
    min_quantity = models.IntegerField(default=0)
    end_date = models.DateTimeField(null=True, blank=True)
    
    description = models.TextField(default="A Quest to be completed by User to earn points.")
    
    def __str__(self) -> str:
        return f'{self.shop.name}_{self.reward_point}pts'