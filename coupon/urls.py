from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('coupons/me/', CouponUserView.as_view()),
    path('coupons/me/<int:pk>/', CouponUserView.as_view()),
    
    path('coupons/my/', CouponShopView.as_view()),
    path('coupons/my/<int:pk>/', CouponShopView.as_view()),
    
    path('defaultcoupons/my/', DefaultCouponShopView.as_view()),
    path('defaultcoupons/my/<int:pk>/', DefaultCouponShopView.as_view()),
    
    path('defaultcoupons/', DefaultCouponManageView.as_view()),
    path('defaultcoupons/<int:pk>/', DefaultCouponManageView.as_view()),
]

"""
{
    "items":[
        {"benefit_set": [8, 4], "exchange_point": 100, "usage_limit": 2},
        {"benefit_set": [5, 6], "exchange_point": 80, "usage_limit": 2},
        {"benefit_set": [7], "exchange_point": 50, "usage_limit": 2},
        {"benefit_set": [5], "exchange_point": 40, "usage_limit": 3},
        {"benefit_set": [5], "exchange_point": 20, "usage_limit": 2}
    ]
}

{
    "items":[
        {"default": 5},
        {"default": 4},
        {"default": 3}
    ]    
}


"""
