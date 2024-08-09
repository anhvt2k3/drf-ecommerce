from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import *
from .serializers import *
from .utils.utils import *
from eco_sys.permissions import IsMerchant
from django.db.models import F


# Create your views here.
class FlashsaleUserView(generics.GenericAPIView):
    pass

class FlashsaleShopView(generics.GenericAPIView):
    pass

class FlashsaleLimitManageView(generics.GenericAPIView):
    pass

class FlashsaleProductView(generics.GenericAPIView):
    pass

class FlashsaleConditionView(generics.GenericAPIView):
    pass

