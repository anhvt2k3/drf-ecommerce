import django_filters
import django_filters.exceptions
from django.db.models import OuterRef, Subquery, CharField, Value, Count
from django.db.models.functions import Coalesce
from .models import Order, OrderItem

class OrderUserFilterSet(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='icontains')
    shop = django_filters.CharFilter(method='filter_by_shop')
    min_items = django_filters.NumberFilter(method='filter_by_min_orderitems')
    
    def filter_by_min_orderitems(self, queryset, name, value):
        return queryset.annotate(
            orderitems_count=Count('orderitem')
        ).filter(orderitems_count__gte=value)
    
    def filter_by_shop(self, queryset, name, value):
        # Subquery to get the shop name of the first OrderItem
        first_order_item_shop = OrderItem.objects.filter(
            order=OuterRef('pk')
        ).values('product__shop__name')[:1]

        # Annotate Order with the first OrderItem's shop name
        queryset = queryset.annotate(
            #@ Coalesce: return '' if Subquery yeild nothing
            first_shop_name=Coalesce(
                Subquery(first_order_item_shop, output_field=CharField()),
                Value('')
            )
        )

        return queryset.filter(first_shop_name__icontains=value)
        
    class Meta:
        model = Order
        fields = ['user', 'status']
    
        
    # def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
    #     super().__init__(data, queryset, request=request, prefix=prefix)
    #     self.validate_filters()
        
    # def validate_filters(self):
    #     minprice = self.data.get('min_price')
    #     maxprice = self.data.get('max_price')
    #     if minprice and float(minprice) < 0:
    #         raise ValueError('Min price cannot be negative.')
    #     if maxprice and float(maxprice) < 0:
    #         raise ValueError('Min price cannot be negative.')
    #     if minprice and maxprice:
    #         if float(minprice) > float(maxprice):
    #             raise ValueError('Minimum price cannot be greater than Maximum price.')