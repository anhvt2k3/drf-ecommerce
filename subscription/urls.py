from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('subscription/my/', PaymentUserView.as_view()),
] 