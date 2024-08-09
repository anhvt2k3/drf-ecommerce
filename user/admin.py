from benefit.models import ConfigBenefit, DefaultBenefit, UserBenefit
from exchange.models import PointExchange
from promotion.models import PromoCondition, Promotion
from quest.models import Quest
from rank.models import Rank, RankConfig
from shop.models import Buyer, PointGain, Progress
from user.models import *
from cart.models import *
from view.models import *
from order.models import *
from coupon.models import *
from product.models import *
from django.apps import apps
from category.models import *
from django.contrib import admin
# Register your models here.
@admin.register(OrderItem)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity', 'price', 'total_charge']
    
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'shop', 'benefits', 'total_charge', 'final_charge','status', 'created_at']
    # list_filter = ['status', 'user']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'in_stock']
    
@admin.register(PointGain)
class PointGainAdmin(admin.ModelAdmin):
    list_display = ['id', 'progress_info','buyer', 'quest', 'current_rank', 'gain_point']
    
@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ['id', 'quest', 'point_gain', 'prog_type', 'goal_value', 'progression']

@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'shop', 'rank', 'total_point', 'remaining_point']

@admin.register(RankConfig)
class RankConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'rank', 'shop', 'required_point', 'enabled', 'is_default']
    
@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'required_point', 'benefits']
        
@admin.register(DefaultBenefit)
class DefaultBenefitAdmin(admin.ModelAdmin):
    list_display = ['id', 'benefit_type', 'benefit_value', 'limitations']
    
@admin.register(ConfigBenefit)
class ConfigBenefitAdmin(admin.ModelAdmin):
    list_display = ['id', 'default_benefit', 'rank_required', 'enabled', 'config_amount', 'config_limit']

@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ['id', 'shop', 'name', 'reward_point', 'product_range', 'min_spent', 'min_quantity', 'end_date']

@admin.register(UserBenefit)
class UserBenefitAdmin(admin.ModelAdmin):
    list_display = ['id', 'benefit', 'shop', 'user', 'is_activate']
    
@admin.register(DefaultCoupon)
class DefaultCouponAdmin(admin.ModelAdmin):
    list_display = ['id', 'exchange_point', 'usage_limit']
    
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['id', 'default', 'shop', 'exchange_point', 'usage_limit']

@admin.register(PromoCondition)
class PromoConditionAdmin(admin.ModelAdmin):
    list_display = ['id', 'promotion', 'defaultPromo', 'cond_type', 'cond_choice', 'cond_min', 'cond_max']

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['id', 'shop', 'name', 'priority', 'start_date', 'end_date', 'benefit_type', 'benefit_value']
@admin.register(PointExchange)
class PointExchangeAdmin(admin.ModelAdmin):
    list_display = ['id', 'buyer', 'coupon', 'remain_usage']
    
for app in apps.get_app_configs():
    for model_name, model in app.models.items(): 
        try:
            admin.site.register(model)
        except admin.sites.AlreadyRegistered:
            pass
