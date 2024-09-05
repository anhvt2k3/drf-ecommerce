from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('payments/me/', PaymentUserView.as_view()),
] 