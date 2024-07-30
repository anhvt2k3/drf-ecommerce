from shop.models import PointGain
import django_filters


class PointGainFilter(django_filters.FilterSet):
    shop = django_filters.CharFilter(field_name='quest__shop__name', lookup_expr='icontains')
    
    class Meta:
        model = PointGain
        fields = ['buyer', 'quest', 'current_rank', 'gain_point']