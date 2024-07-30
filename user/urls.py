from rest_framework.urlpatterns import path, include
from rest_framework.routers import DefaultRouter
from .views import *

urlpatterns = [
    path('register/', UserRegisterView.as_view()),
    path('login/', UserLoginView.as_view(), name='login'),
    
    path('auth/google/', GoogleAuthView.as_view()),
    path('callback/google/', GoogleCallbackView.as_view()),
    path('auth/facebook/', FacebookAuthView.as_view()),
    path('callback/facebook/', FacebookCallbackView.as_view()),
    # path('auth/callback/google/', GoogleValidateView.as_view()),
    
    path('users/me/', UserLoggedView.as_view(), name='me'),
    
    path('users/', UserManageView.as_view()),
    path('users/<int:pk>/', UserManageView.as_view()),
]

"""
{
    
}

user fields[
    "logentry",
    "shop",
    "buyer",
    "userbenefit",
    "cart",
    "view",
    "order",
    "id",
    "last_login",
    "is_superuser",
    "first_name",
    "last_name",
    "email",
    "is_staff",
    "is_active",
    "date_joined",
    "created_at",
    "updated_at",
    "is_deleted",
    "username",
    "password",
    "phone",
    "address",
    "is_merchant",
    "description",
    "groups",
    "user_permissions"
]
"""
