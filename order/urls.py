from .views import *
from rest_framework.urlpatterns import path, include


urlpatterns = [
    path('orderitems/me/', OrderItemUserView.as_view()),
    path('orderitems/me/<int:pk>/', OrderItemUserView.as_view()),
    path('orderitems/my/', OrderItemShopView.as_view()),
    path('orderitems/my/<int:pk>/', OrderItemShopView.as_view()),
    path('checkout/me/', CheckoutView.as_view()),
    
    path('pay/', PaymentView.as_view()),
    # path('pay-success/', PaymentSuccessView.as_view()),
    # path('pay-cancel/', PaymentCancelView.as_view()),
    
    path('orders/me/', OrderUserView.as_view()),
    path('orders/me/<int:pk>/', OrderUserView.as_view()),
    path('orders/my/', OrderShopView.as_view()),
    path('orders/my/<int:pk>/', OrderShopView.as_view()),
    
    path('orders/', OrderManageView.as_view()),
    path('orders/<int:pk>/', OrderManageView.as_view()),
    path('orderitems/', OrderManageView.as_view()),
    path('orderitems/<int:pk>/', OrderManageView.as_view()),
]


"""
{
    "coupon": null,
    "items": [
        {
            "product": 98,
            "quantity": 1
        },
        {
            "product": 99,
            "quantity": 1
        },
        {
            "product": 100,
            "quantity": 1
        },
        {
            "product": 101,
            "quantity": 1
        }
    ]
}



        orderitems = [
            {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.product.name,
                    },
                    'unit_amount': int(item.price * 100),  # Convert dollars to cents
                },
                'quantity': item.quantity,
            }
            for item in order.orderitem_set.all()]
        if order.final_charge != order.total_charge:
            orderitems.append(
            {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Discount',
                    },
                    'unit_amount': int((order.total_charge - order.final_charge) * 100),  # Convert dollars to cents
                },
                'quantity': 1,
            })
"""