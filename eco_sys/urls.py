"""
URL configuration for eco_sys project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from .views import DebugView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('debug/', DebugView.as_view()),
    path('', include('notification.urls')),
    path('', include('flashsale.urls')),
    path('', include('promotion.urls')),
    path('', include('exchange.urls')),
    path('', include('quest.urls')),
    path('', include('shop.urls')),
    path('', include('rank.urls')),
    path('', include('user.urls')),
    path('', include('category.urls')),
    path('', include('coupon.urls')),
    path('', include('product.urls')),
    path('', include('order.urls')),
    path('', include('cart.urls')),
    path('', include('view.urls')),
    path('', include('benefit.urls')),
    
]
