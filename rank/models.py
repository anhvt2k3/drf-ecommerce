from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin

# Create your models here.
class Rank(SoftDeleteModelMixin, models.Model):
    name = models.CharField(max_length=100, unique=True)
    required_point = models.IntegerField(default=0)
    benefits = models.JSONField(default=list)
    description = models.TextField(default="A Rank in the Ecommerce System.")
    
    def __str__(self) -> str:
        return f'{self.name}_{self.required_point}'
    
class RankConfig(SoftDeleteModelMixin, models.Model):
    rank = models.ForeignKey(Rank, on_delete=models.CASCADE)
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    required_point = models.IntegerField(default=0)
    enabled = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    description = models.TextField(default="A configuration of Rank different between Shops.")
    
    def __str__(self) -> str:
        return f'{self.rank.name}_[{self.shop}]'