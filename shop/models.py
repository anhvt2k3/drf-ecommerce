from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin

# Create your models here.
class Shop(SoftDeleteModelMixin, models.Model):
    name = models.CharField(max_length=100)
    merchant = models.ForeignKey('user.User', on_delete=models.CASCADE)
    
    description = models.TextField(default="A Shop in the Ecommerce System.")    
    
    def __str__(self) -> str:
        return self.name
    
class Buyer(SoftDeleteModelMixin, models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    rank = models.ForeignKey('rank.RankConfig', on_delete=models.CASCADE)
    total_point = models.IntegerField(default=0)
    
    description = models.TextField(default="A User who is interested with the Shop activities.")


class PointGain(SoftDeleteModelMixin, models.Model):
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    quest = models.ForeignKey('quest.Quest', on_delete=models.CASCADE)
    current_rank = models.CharField(max_length=100)
    gain_point = models.IntegerField(default=0)
    orderitems = models.JSONField(default=list)
    
    description = models.TextField(default="A record of Point gaining in completing Actions.")
    
    def insert_orderitem(self, orderitem):
        if orderitem not in self.orderitems:
            self.orderitems.append(orderitem)
        self.save()
        
    
class Progress(SoftDeleteModelMixin, models.Model):
    point_gain = models.ForeignKey(PointGain, on_delete=models.CASCADE)
    prog_type = models.CharField(max_length=100)
    goal_value = models.FloatField(default=0)
    progression = models.FloatField(default=0)
    
