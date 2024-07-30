from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('exchanges/me/', PointExchangeUserView.as_view()),
    path('exchanges/me/<int:pk>/', PointExchangeUserView.as_view()),
    
    path('exchanges/my/', PointExchangeShopView.as_view()),
    path('exchanges/my/<int:pk>/', PointExchangeShopView.as_view()),
    
    # path('exchanges/', ExchangeManageView.as_view()),
    # path('exchanges/<int:pk>/', ExchangeManageView.as_view()),
] 