from rest_framework.urlpatterns import path, include
from .views import *


urlpatterns = [
    path('categories/me/', CategoryUserView.as_view()),
    path('categories/me/<int:pk>/', CategoryUserView.as_view()),
    
    path('categories/', CategoryManageView.as_view()),   
    path('categories/<int:pk>/', CategoryManageView.as_view()),   
    
]

