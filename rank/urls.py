from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('ranks/me/', RankShopView.as_view()),
    path('ranks/me/<int:pk>/', RankShopView.as_view()),
    path('ranks/', RankManageView.as_view()),
    path('ranks/<int:pk>/', RankManageView.as_view()),
    
    path('rankconfs/me/', RankConfigBuyerView.as_view()),
    path('rankconfs/me/<int:pk>/', RankConfigBuyerView.as_view()),
    
    path('rankconfs/my/', RankConfigShopView.as_view()),
    path('rankconfs/my/<int:pk>/', RankConfigShopView.as_view()),
    path('rankconfs/', RankConfigManageView.as_view()),
    path('rankconfs/<int:pk>/', RankConfigManageView.as_view()),
    # path('products/push', ProductCUDView.as_view(),  name='Product-create'),
    # path('products/update/<int:pk>', ProductCUDView.as_view(),  name='Product-update'),
    # path('products/delete/<int:pk>', ProductCUDView.as_view(),  name='Product-delete'),
]

"""
{
    "items" : [
        {"name": "Iron", "required_point": 50, "benefits": "A 10% coupon for first item of day."},
        {"name": "Bronze", "required_point": 100, "benefits": "A 20% coupon for first item of day."},
        {"name": "Silver", "required_point": 200, "benefits": "A 40% coupon for first item of day."},
        {"name": "Emerald", "required_point": 500, "benefits": "A 50% coupon for first item of day."},
        {"name": "Gold", "required_point": 600, "benefits": "A 60% coupon for first item of day."}
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