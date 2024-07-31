from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin

# Create your models here.
class DefaultBenefit(SoftDeleteModelMixin, models.Model):
    benefit_type = models.CharField(max_length=200)
    benefit_value = models.FloatField(default=0)
    limitations = models.JSONField(default=dict, blank=True, null=True)
    description = models.TextField(default="Default Benefit created by Admin for all Shop to utilize.")

    def __str__(self) -> str:
        return f'DefaultBenefit[{self.id}]: {self.benefit_type}'

class ConfigBenefit(SoftDeleteModelMixin, models.Model):
    default_benefit = models.ForeignKey(DefaultBenefit, on_delete=models.CASCADE)
    rank_required = models.ForeignKey('rank.RankConfig', on_delete=models.CASCADE)
    enabled = models.BooleanField(default=True)
    config_amount = models.FloatField()
    config_limit = models.JSONField(default=dict)
    
    description = models.TextField(default="Benefit Configuration created by Shops to apply to their Buyers of certain Ranks.")
    
    def __str__(self) -> str:
        return f'Benefit[{self.id}] from Rank[{self.rank_required.rank.name}]'
    
class UserBenefit(SoftDeleteModelMixin, models.Model):
    benefit = models.ForeignKey(ConfigBenefit, on_delete=models.CASCADE)
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    is_activate = models.BooleanField(default=True)
    
    description = models.TextField(default="A record of acquired benefits for Users.")