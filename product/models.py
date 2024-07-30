from typing import Any
from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin
from category.models import Category

# Create your models here.
class Product(SoftDeleteModelMixin, models.Model):
    name = models.CharField(max_length=255)
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE, null=True, blank=True)
    price = models.FloatField()
    in_stock = models.BigIntegerField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
    description = models.TextField(default="A Product of the Ecommerce System.")
    image = models.ImageField()
    
    
    def __str__(self):
        return f'{self.name}[{self.id}]_{self.shop.name if self.shop else "No Shop"}'