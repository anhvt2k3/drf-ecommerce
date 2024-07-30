from typing import Any
from django.db import models
from eco_sys.mixins import ChildrenOfTableMixin, SoftDeleteModelMixin

# Create your models here.
class Cart(SoftDeleteModelMixin, models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    
    description = models.TextField(default="A Cart which is created by User that consists of many Cart Items.")
    
    
    
class CartItem(SoftDeleteModelMixin, models.Model, ChildrenOfTableMixin):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    quantity = models.BigIntegerField()
    price = models.FloatField()
    
    description = models.TextField(default="A Cart Item which is created by User that linked to a Product.")
    
    
    # class Meta:
    #     constraints = [
    #                 models.UniqueConstraint(fields=['cart', 'product'], name='unique_cart_product')
    #     ]