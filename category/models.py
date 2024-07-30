from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin

# Create your models here.
class Category(SoftDeleteModelMixin, models.Model):
    name = models.CharField(max_length=255, unique=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    description = models.TextField(default="A Category of the Ecommerce System to help Admin categorize Products.")
    
    
    
    def __str__(self):
        return self.name