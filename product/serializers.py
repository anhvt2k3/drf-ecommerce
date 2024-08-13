
from shop.models import Shop
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers

class ProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    price = serializers.FloatField()
    in_stock = serializers.IntegerField()
    
    def validate(self, data):
        # print ('validating: ',data)
        return data
    
    def create(self, validated_data):
        # print ('creating:', validated_data)
        instance_class = self
        model = Product
        validated_data = validated_data
        #! Create instance with required fields from Serialier class.
        fields = validated_data.keys()
        args = {}
        for field in fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()
        return instance
    
    def update(self, instance, validated_data):
        # print ('updating:', [f.name for f in instance._meta.fields], validated_data)
        instance = instance
        validated_data = validated_data
        exclude_fields = ['id']
        #! Update instance with fields from validated_data without the exclude fields.
        instance_fields = [field.name for field in instance._meta.fields]
        fields = [field for field in validated_data.keys() if field not in exclude_fields and field in instance_fields]
        for field in fields:
            value = validated_data.get(field) if field in validated_data else instance.__getattribute__(field)
            instance.__setattr__(field, value)
        instance.save()
        return instance
    
    def delete(self, instance=None):
        instance = instance or self.instance
        instance.delete()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['name', 'price', 'in_stock'],
                instance=instance),
            'shop': instance.shop.name if instance.shop else None,
            'category': instance.category.name if instance.category else None,
            'view_times': instance.viewitem_set.count(),
            'cart_times': instance.cartitem_set.count(),
            'order_times': instance.orderitem_set.count(),
        }
        
class ProductDetailSerializer(ProductSerializer):
    def to_representation(self, instance):
        from cart.serializers import CartItemSerializer
        from order.serializers import OrderItemSerializer
        from view.serializers import ViewItemSerializer
        from category.serializers import CategorySerializer
        from shop.serializers import ShopSerializer
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['name', 'price', 'in_stock'],
                instance=instance),
            'shop': ShopSerializer(instance.shop).data if instance.shop else None,
            'category': CategorySerializer(instance.category).data if instance.category else None,
            'viewed_as_item': ViewItemSerializer(instance.viewitem_set.all(), many=True).data,
            'carted_as_item': CartItemSerializer(instance.cartitem_set.all(), many=True).data,
            'ordered_as_item': OrderItemSerializer(instance.orderitem_set.all(), many=True).data,
        }
        
class ProductUserSerializer(ProductSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['name', 'price', 'in_stock'],
                instance=instance),
            'shop': instance.shop.name if instance.shop else None,
            'category': instance.category.name if instance.category else None,
        }
        