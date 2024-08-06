from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin
from shop.models import Shop
from user.models import User

# Create your models here.
class Notification(SoftDeleteModelMixin, models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    message = models.TextField()
    link = models.URLField(null=True, blank=True)
    read_status = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    additional_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f'Nofi[{self.type}:{self.title}] for User[{self.recipient.username}]'