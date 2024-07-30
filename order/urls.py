from .views import *
from rest_framework.urlpatterns import path, include


urlpatterns = [
    path('orderitems/me/', OrderItemUserView.as_view()),
    path('orderitems/me/<int:pk>/', OrderItemUserView.as_view()),
    path('orderitems/my/', OrderItemShopView.as_view()),
    path('orderitems/my/<int:pk>/', OrderItemShopView.as_view()),
    
    path('orders/me/', OrderUserView.as_view()),
    path('orders/me/<int:pk>/', OrderUserView.as_view()),
    path('orders/my/', OrderShopView.as_view()),
    path('orders/my/<int:pk>/', OrderShopView.as_view()),
    
    path('orders/', OrderManageView.as_view()),
    path('orders/<int:pk>/', OrderManageView.as_view()),
    path('orderitems/', OrderManageView.as_view()),
    path('orderitems/<int:pk>/', OrderManageView.as_view()),
]


