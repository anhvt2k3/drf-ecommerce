from django.db import models
from user.models import User
from product.models import Product
from eco_sys.mixins import SoftDeleteModelMixin

# Create your models here.
class View(SoftDeleteModelMixin, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    description = models.TextField()
    
    
class ViewItem(SoftDeleteModelMixin, models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    view =  models.ForeignKey(View, on_delete=models.CASCADE)
    
    description = models.TextField()
    
    
    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(fields=['product', 'view'], name='unique_product_view')
    #     ]
    