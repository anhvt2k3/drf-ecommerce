from rest_framework.urlpatterns import path, include
from .views import *

urlpatterns = [
    path('subscriptions/my/', SubscriptionMerchantView.as_view()),
] 

""" 
Limit Design Dictionary:
    - day-cap: The maximum number of instance of a service can be created in 1 day
    - week-cap: The maximum number of instance of a service can be created in 1 week
    - access: The level of access to a service, 
        'none' : access is not allowed,
        'limited' : access is allowed with limits,
        'unlimited' : access is allowed without any limits
        
Limit - Progression Mapping:
    - 'day-cap' ->
    

    'Basic': {
        'Flashsale': {
            'access': 'limited',   # Limited access to flashsale
            'day-cap': 1,          # 1 flashsale allowed per day
            'week-cap': 5          # 5 flashsales allowed per week
        },
        'Promotion': {
            'access': 'limited',   # Limited access to flashsale
            'day-cap': 2,          # 2 promotions allowed per day
            'week-cap': 10         # 10 promotions allowed per week
        },
        'Notification': {
            'access': 'limited',   # Limited access to flashsale
            'day-cap': 5,          # 5 notifications allowed per day
            'week-cap': 35         # 35 notifications allowed per week
        },
        'Loyalty Program': {
            'access': 'none' # Limited loyalty program access
        }
    },
    'Personal': {
        'Flashsale': {
            'access': 'limited',   # Limited access to flashsale
            'day-cap': 3,          # 3 flashsales allowed per day
            'week-cap': 15         # 15 flashsales allowed per week
        },
        'Promotion': {
            'access': 'limited',   # Limited access to flashsale
            'day-cap': 5,          # 5 promotions allowed per day
            'week-cap': 25         # 25 promotions allowed per week
        },
        'Notification': {
            'access': 'limited',   # Limited access to flashsale
            'day-cap': 10,         # 10 notifications allowed per day
            'week-cap': 70         # 70 notifications allowed per week
        },
        'Loyalty Program': {
            'access': 'none' # Limited loyalty program access
        }
    },
    'Business': {
        'Flashsale': {
            'access': 'limited',   # Limited access to flashsale
            'day-cap': 10,         # 10 flashsales allowed per day
            'week-cap': 50         # 50 flashsales allowed per week
        },
        'Promotion': {
            'access': 'limited',   # Limited access to flashsale
            'day-cap': 10,         # 10 promotions allowed per day
            'week-cap': 50         # 50 promotions allowed per week
        },
        'Notification': {
            'access': 'limited',   # Limited access to flashsale
            'day-cap': 20,         # 20 notifications allowed per day
            'week-cap': 140        # 140 notifications allowed per week
        },
        'Loyalty Program': {
            'access': 'unlimited'  # Full loyalty program access
        }
"""
