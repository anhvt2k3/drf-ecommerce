from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin

# Create your models here.
class Refund(SoftDeleteModelMixin, models.Model):
    order = models.ForeignKey('order.Order', on_delete=models.CASCADE)
    cause = models.TextField(default="No cause provided")
    contacts = models.JSONField(default=dict)
    confirmation = models.BooleanField(default=False)
    
    description = models.TextField(default="A Refund object of the Ecommerce System.")
    
    def __str__(self) -> str:
        return f"Refund of {self.order}"