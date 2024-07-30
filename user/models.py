from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from eco_sys.mixins import SoftDeleteModelMixin
# Create your models here.

AUTH_PROVIDERS = {'email': 'email', 'google': 'google'}

class User(AbstractUser, SoftDeleteModelMixin ):
    username = models.EmailField(max_length=50, unique=True)
    password = models.CharField(max_length=255, default="unused-password")
    
    phone = models.CharField(max_length=10, blank=True, null=True)
    address = models.TextField(max_length=100, blank=True, null=True)
    is_merchant = models.BooleanField(
        _("merchant status"),
        default=False,
        help_text=_("Designates whether the user is a shop owner qualified to manage products."))
    
    auth_provider = models.CharField(
        max_length=255, blank=False,
        null=False, default=AUTH_PROVIDERS.get('email'))
    
    description = models.TextField(default="A User of the Ecommerce System.")

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    
    def __str__(self):
        return self.username