import django_filters
from .models import Coupon 


class CouponFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter(field_name='id', lookup_expr='exact')
    shop = django_filters.CharFilter(field_name='shop__name', lookup_expr='icontains')
    
    class Meta:
        model = Coupon
        fields = ['id', 'shop']