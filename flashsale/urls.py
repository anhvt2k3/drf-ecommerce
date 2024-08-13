from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('flashsalelimits/my/', FlashsaleLimitShopView.as_view()),
    path('flashsalelimits/my/<int:pk>/', FlashsaleLimitShopView.as_view()),
    path('flashsalelimits/', FlashsaleLimitManageView.as_view()),
    path('flashsalelimits/<int:pk>/', FlashsaleLimitManageView.as_view()),
    
    path('flashsaleproducts/my/', FlashsaleProductView.as_view()),
    path('flashsaleconditions/my/', FlashsaleConditionView.as_view()),
    path('flashsales/my/', FlashsaleShopView.as_view()),
    path('flashsales/my/<int:pk>/', FlashsaleShopView.as_view()),
    
    path('flashsales/me/', FlashsaleUserView.as_view()),
    path('flashsales/me/<int:pk>/', FlashsaleUserView.as_view()),
]

"""
{
    "items": [
        {
            "type": "product:max-sales",
            "value": 1,
            "unit": "sales"
        },
        {
            "type": "sale:max-period",
            "value": 1,
            "unit": "hours"
        }
}

{
    "name": "Bankrupt Flashsale",
    "start_date": "2024-08-15T10:00:00Z",
    "end_date": "2024-08-15T11:00:00Z",
    "products": [
        {
            "product": 101,
            "stock": 500,
            "sale_price": ,
            "sale_limit": 
        }
    ],
    "conditions": [
        {
            "type": ,
            "min": ,
            "max": ,
            "choice": 
        }
    ]
}

{
    "defaultPromo": 4,    
}


"""