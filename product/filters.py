import django_filters
import django_filters.exceptions
from .models import Product

class ProductAdminFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name',lookup_expr='icontains')
    category = django_filters.CharFilter(field_name='category.name',lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    updated_before = django_filters.DateFilter(field_name='updated_at', lookup_expr='lte')
    updated_after = django_filters.DateFilter(field_name='updated_at', lookup_expr='gte')
    
    
    class Meta:
        model = Product
        fields = ['name', 'price', 'category', 'in_stock', 'created_at', 'updated_at', 'min_price', 'max_price', 'created_before', 'created_after', 'updated_before', 'updated_after']
        
    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.validate_filters()
        
    def validate_filters(self):
        minprice = self.data.get('min_price')
        maxprice = self.data.get('max_price')
        if minprice and float(minprice) < 0:
            raise ValueError('Min price cannot be negative.')
        if maxprice and float(maxprice) < 0:
            raise ValueError('Min price cannot be negative.')
        if minprice and maxprice:
            if float(minprice) > float(maxprice):
                raise ValueError('Minimum price cannot be greater than Maximum price.')

class ProductUserFilter(ProductAdminFilter):
    
    class Meta:
        model = Product
        fields = ['name', 'price', 'category', 'in_stock', 'min_price', 'max_price']