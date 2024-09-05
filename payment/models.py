from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin

# Create your models here.
class Payment(SoftDeleteModelMixin, models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    type = models.CharField(max_length=10)
    method_object = models.JSONField(default=dict)
    
    