from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('notifications/me/', NotificationUserView.as_view(), name='notification'),
] 