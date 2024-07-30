from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('quests/me/', QuestUserView.as_view(),  name='Product-getall'),
    path('quests/me/<int:pk>/', QuestUserView.as_view(),  name='Product-get'),
    
    path('quests/my/', QuestShopView.as_view(),  name='Product-getall'),
    path('quests/my/<int:pk>/', QuestShopView.as_view(),  name='Product-get'),
    
    path('quests/', QuestManageView.as_view(),  name='Product-create'),
    path('quests/<int:pk>/', QuestManageView.as_view(),  name='Product-get'),
    # path('products/push', ProductCUDView.as_view(),  name='Product-create'),
    # path('products/update/<int:pk>', ProductCUDView.as_view(),  name='Product-update'),
    # path('products/delete/<int:pk>', ProductCUDView.as_view(),  name='Product-delete'),
]

"""
{
    "items" : [
        {
            "name": "Buy 3 products from shop",
            "reward_point": 10,
            "product_range": "__all__",
            "min_spent": 0,
            "min_quantity": 3
        },
        {
            "name": "Spend 300$ on shop",
            "reward_point": 50,
            "product_range": "__all__",
            "min_spent": 300,
            "min_quantity": 0
        },
        {
            "name": "Buy 4 products from shop",
            "reward_point": 30,
            "product_range": "__all__",
            "min_spent": 0,
            "min_quantity": 4
        }
        
    ]    
}

"""