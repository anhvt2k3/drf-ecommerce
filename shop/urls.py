from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('shops/my/', ShopMerchantView.as_view(),  name='Product-getall'),
    path('shops/my/<int:pk>/', ShopMerchantView.as_view(),  name='Product-get'),
    
    path('buyers/my/', BuyerShopView.as_view(),  name='Product-getall'),
    path('buyers/my/<int:pk>/', BuyerShopView.as_view(),  name='Product-get'),
    path('buyers/me/', BuyerUserView.as_view(),  name='Product-getall'),
    path('buyers/me/<int:pk>/', BuyerUserView.as_view(),  name='Product-get'),
    
    path('pointgain/me/', PointGainBuyerView.as_view(),  name='Product-getall'),
    path('pointgain/me/<int:pk>/', PointGainBuyerView.as_view(),  name='Product-get'),
    path('pointgain/my/', PointGainShopView.as_view(),  name='Product-getall'),
    path('pointgain/my/<int:pk>/', PointGainShopView.as_view(),  name='Product-get'),
    
    path('shops/', ShopManageView.as_view(),  name='Product-create'),
    path('shops/<int:pk>/', ShopManageView.as_view(),  name='Product-get'),
    # path('products/push', ProductCUDView.as_view(),  name='Product-create'),
    # path('products/update/<int:pk>', ProductCUDView.as_view(),  name='Product-update'),
    # path('products/delete/<int:pk>', ProductCUDView.as_view(),  name='Product-delete'),
]
