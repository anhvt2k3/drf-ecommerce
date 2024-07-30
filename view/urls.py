from .views import *
from rest_framework.urlpatterns import path, include

urlpatterns = [
    path('viewitems/me/', ViewItemUserView.as_view()),
    path('viewitems/me/<int:pk>/', ViewItemUserView.as_view()),
    path('views/me/', ViewUserView.as_view()),
    
    path('viewitems/', ViewItemManageView.as_view()),
    path('viewitems/<int:pk>/', ViewItemManageView.as_view()),
    path('views/<int:pk>/', ViewManageView.as_view()),
    path('views/', ViewManageView.as_view()),
]
