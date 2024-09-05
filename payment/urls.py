from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('payment/me/', PaymentUserView.as_view()),
] 