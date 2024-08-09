from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('flashsales/my/', FlashsaleShopView.as_view()),
    path('flashsales/my/<int:pk>/', FlashsaleShopView.as_view()),
    path('flashsales/', FlashsaleLimitManageView.as_view()),
    path('flashsales/<int:pk>/', FlashsaleLimitManageView.as_view()),
    
    path('flashsales/me/', FlashsaleUserView.as_view()),
    path('flashsales/me/<int:pk>/', FlashsaleUserView.as_view()),
    
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

{
    "name": "Summer Sale",
    "benefit_type": "percentage",
    "benefit_value": "0.2",
    "defaultPromo": 4,
    "conditions": [
        {
            "cond_type": "charge",
            "cond_choice": null,
            "cond_min": 100.0
        },
        {
            "cond_type": "quantity",
            "cond_choice": null,
            "cond_min": 2
        }
    ]
}

{
    "defaultPromo": 4,    
}


"""