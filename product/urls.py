from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('products/me/', ProductUserView.as_view(),  name='Product-getall'),
    path('products/me/<int:pk>/', ProductUserView.as_view(),  name='Product-get'),
    
    path('products/my/', ProductShopView.as_view(),  name='Product-getall'),
    path('products/my/<int:pk>/', ProductShopView.as_view(),  name='Product-get'),
    
    path('products/', ProductManageView.as_view(),  name='Product-create'),
    path('products/<int:pk>/', ProductManageView.as_view(),  name='Product-get'),
    # path('products/push', ProductCUDView.as_view(),  name='Product-create'),
    # path('products/update/<int:pk>', ProductCUDView.as_view(),  name='Product-update'),
    # path('products/delete/<int:pk>', ProductCUDView.as_view(),  name='Product-delete'),
] 