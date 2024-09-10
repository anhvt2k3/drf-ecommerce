from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('refunds/me/', RefundUserView.as_view(),  name='refund-getall'),
    path('refunds/me/<int:pk>/', RefundUserView.as_view(),  name='refund-get'),\
        
    path('refunds/my/', RefundShopView.as_view(),  name='refund-getall'),
    path('refunds/my/<int:pk>/', RefundShopView.as_view(),  name='refund-get'),
] 