from benefit.models import DefaultBenefit
from notification.models import Notification
from notification.serializers import NotificationSerializer
from product.models import Product
from shop.models import Shop
from shop.serializers import ShopDetailSerializer, ShopSerializer
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers


class FlashsaleLimitSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=200)
    value = serializers.FloatField(default=0)
    unit = serializers.CharField(max_length=200)
    
    def create(self, validated_data):
        instance = FlashsaleLimit.objects.create(**validated_data)
        return instance
    
    def update(self, instance, validated_data):
        instance = instance
        instance.type = validated_data.get('type', instance.type)
        instance.value = validated_data.get('value', instance.value)
        instance.unit = validated_data.get('unit', instance.unit)
        instance.save()
        return instance
    
    def delete(self, instance=None):
        instance = instance or self.instance
        instance.delete()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['type', 'value', 'unit'],
                instance=instance),
        }

class FlashsaleProductSerializer(serializers.Serializer):
    flashsale = serializers.PrimaryKeyRelatedField(queryset=Flashsale.objects.all(), required=False)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    stock = serializers.IntegerField(default=0)
    sale_price = serializers.FloatField(default=0)
    sale_limit = serializers.IntegerField(default=0) # limit quantity per buyer
    
    def create(self, validated_data):
        instance = FlashsaleProduct.objects.create(**validated_data)
        return instance
    
    def update(self, instance, validated_data):
        instance = instance
        instance.stock = validated_data.get('stock', instance.stock)
        instance.sale_price = validated_data.get('sale_price', instance.sale_price)
        instance.sale_limit = validated_data.get('sale_limit', instance.sale_limit)
        instance.save()
        return instance
    
    def delete(self, instance=None):
        instance = instance or self.instance
        instance.delete()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['stock', 'sale_price', 'sale_limit'],
                instance=instance),
        }
        
class FlashsaleConditionSerializer(serializers.Serializer):
    flashsale = serializers.PrimaryKeyRelatedField(queryset=Flashsale.objects.all(), required=False)
    type = serializers.CharField(max_length=200)
    min = serializers.FloatField(default=0)
    max = serializers.FloatField(default=0)
    choice = serializers.JSONField(default=list, blank=True, null=True)
    
    def create(self, validated_data):
        instance = FlashsaleCondition.objects.create(**validated_data)
        return instance
    
    def update(self, instance, validated_data):
        instance = instance
        instance.type = validated_data.get('type', instance.type)
        instance.min = validated_data.get('min', instance.min)
        instance.max = validated_data.get('max', instance.max)
        instance.choice = validated_data.get('choice', instance.choice)
        instance.save()
        return instance
    
    def delete(self, instance=None):
        instance = instance or self.instance
        instance.delete()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['type', 'min', 'max', 'choice'],
                instance=instance),
        }

class FlashsaleSerializer(serializers.Serializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    name = serializers.CharField(max_length=200)
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    
    products = FlashsaleProductSerializer(many=True, required=False)
    conditions = FlashsaleConditionSerializer(many=True, required=False)
    
    def validate(self, data):
        
        return data
    
    def create(self, validated_data):
        products = validated_data.pop('products', [])
        instance = Flashsale.objects.create(**validated_data)
        for product in products:
            FlashsaleProduct.objects.create(flashsale=instance, **product)
            FlashsaleCondition.objects.create(flashsale=instance, **product)
        return instance
    
    def update(self, instance, validated_data):
        instance = instance
        instance.name = validated_data.get('name', instance.name)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.end_date = validated_data.get('end_date', instance.end_date)
        instance.save()
        return instance
    
    def delete(self, instance=None):
        instance = instance or self.instance
        instance.delete()
        return instance
    