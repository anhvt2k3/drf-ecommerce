from .views import *
from rest_framework.urlpatterns import path, include


urlpatterns = [
    path('webhooks/stripe/', PaymentStripeWebhookView.as_view()),
]
