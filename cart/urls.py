from .views import *
from rest_framework.urlpatterns import path, include

urlpatterns = [
    path('carts/me/', CartUserView.as_view()),
    path('cartitems/me/', CartItemUserView.as_view()),
    path('cartitems/me/<int:pk>/', CartItemUserView.as_view()),
    
    path('carts/', CartManageView.as_view()),
    path('carts/<int:pk>/', CartManageView.as_view()),
    path('cartitems/', CartItemManageView.as_view()),
    path('cartitems/<int:pk>/', CartItemManageView.as_view()),
]