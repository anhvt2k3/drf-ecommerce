from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('defaultbenefits/my/', DefaultBenefitShopView.as_view()),
    path('defaultbenefits/my/<int:pk>/', DefaultBenefitShopView.as_view()),
    path('defaultbenefits/', DefaultBenefitManageView.as_view()),
    path('defaultbenefits/<int:pk>/', DefaultBenefitManageView.as_view()),
    
    path('benefits/me/', BenefitUserView.as_view()),
    path('benefits/me/<int:pk>/', BenefitUserView.as_view()),
    
    
    path('benefits/my/', BenefitsShopView.as_view()),
    path('benefits/my/<int:pk>/', BenefitsShopView.as_view()),
    path('benefitcfs/my/', BenefitConfigShopView.as_view()),
    path('benefitcfs/my/<int:pk>/', BenefitConfigShopView.as_view()),
    # path('products/push', ProductCUDView.as_view(),  name='Product-create'),
    # path('products/update/<int:pk>', ProductCUDView.as_view(),  name='Product-update'),
    # path('products/delete/<int:pk>', ProductCUDView.as_view(),  name='Product-delete'),
]

"""
{
    "items" : [
        {"discount_type": "direct", "discount_amount": 200},
        {"discount_type": "direct", "discount_amount": 150},
        {"discount_type": "direct", "discount_amount": 100},
        {"discount_type": "direct", "discount_amount": 70},
        {"discount_type": "direct", "discount_amount": 50},
        {"discount_type": "percentage", "discount_amount": 0.15},
        {"discount_type": "percentage", "discount_amount": 0.3},
        {"discount_type": "percentage", "discount_amount": 0.5},
        {"discount_type": "percentage", "discount_amount": 0.7}
    ]
}

{
    "items" : [
        {"id": 1, "name": "Irony"}
        ]    
}

{
    "items" : [
        {"rank": 1},
        {"rank": 2},
        {"rank": 3}
    ]    
}

{
    "rank": 1,
    "required_point": 100,
    "enabled": 0,
}
"""