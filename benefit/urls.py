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
        {"benefit_type": "direct", "benefit_value": 200},
        {"benefit_type": "direct", "benefit_value": 150},
        {"benefit_type": "direct", "benefit_value": 100},
        {"benefit_type": "direct", "benefit_value": 70},
        {"benefit_type": "direct", "benefit_value": 50},
        {"benefit_type": "percentage", "benefit_value": 0.15},
        {"benefit_type": "percentage", "benefit_value": 0.3},
        {"benefit_type": "percentage", "benefit_value": 0.5},
        {"benefit_type": "percentage", "benefit_value": 0.7}
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