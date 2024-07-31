from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('defaultpromo/my/', DefaultPromotionShopView.as_view()),
    path('defaultpromo/my/<int:pk>/', DefaultPromotionShopView.as_view()),
    path('defaultpromo/', DefaultPromotionManageView.as_view()),
    path('defaultpromo/<int:pk>/', DefaultPromotionManageView.as_view()),
    
    path('promo/me/', PromotionUserView.as_view()),
    path('promo/me/<int:pk>/', PromotionUserView.as_view()),
    
    
    path('promo/my/', PromotionShopView.as_view()),
    path('promo/my/<int:pk>/', PromotionShopView.as_view()),
]

"""
{
    "name": "Winter Sale",
    "benefit_type": "percentage",
    "benefit_value": 0.15,
    "conditions": [
        {
            "cond_type": "charge",
            "cond_choice": null,
            "cond_min": 50.0
        },
        {
            "cond_type": "item_quantity",
            "cond_choice": null,
            "cond_min": 3
        }
    ]
}


"""