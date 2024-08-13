from product.models import Product
from shop.models import Shop
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers

"""
!Flashsale Flow:
    ?Merchant-side:
        > Decide the Flashsale name, start_date, end_date
        > Add preferred products to the Flashsale:
            - product : id
            - stock : int
            - sale_price : float
            - sale_limit : int
        > Add conditions to the Flashsale:
            - type : str
            - min : float
            - max : float
            - choice : list
        > Validate Flashsale products by FlashsaleLimit
        > Validate Flashsale conditions by FlashsaleLimit
        > Validate Flashsale by FlashsaleLimit
        > Create Flashsale and its related products and conditions
        > Create Flashsale Notification to Buyers
    ?Customer-side:
        > Receive Flashsale Notification
        > Check Flashsale products and conditions
        > Checkout Order with Flashsale products
        >> With preferred Flashsale and Coupon
            > Validate Flashsale products with conditions
            > Apply Checkout.logics
                > Applying Flashsale leaving out Promotions
        > Compare prices and approve Order
        > Create Order
        >> With preferred Flashsale and Coupon
            > Validate Flashsale products with conditions
            > Apply Order.logics
                > Applying Flashsale leaving out Promotions
            > Store Flashsale onto OrderBenefits
        > User check their Orders
"""
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
        
class FlashsaleLimitDetailSerializer(FlashsaleLimitSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['type', 'value', 'unit'],
                instance=instance),
        }


class FlashsaleProductSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    stock = serializers.IntegerField(default=0, min_value=0)
    sale_price = serializers.FloatField(default=0, min_value=0)
    sale_limit = serializers.IntegerField(default=0) # limit quantity per buyer
    
    def validate(self, data):
        if self.instance: return data
        if data['sale_limit'] > data['stock']:
            raise serializers.ValidationError('Sale limit is over the stock')
        if data['sale_price'] > data['product'].price:
            raise serializers.ValidationError('Sale price is over the product price')
        if data['stock'] > data['product'].in_stock:
            raise serializers.ValidationError('Stock is over the product stock')
        return data
    
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
        
class FlashsaleProductDetailSerializer(FlashsaleProductSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['stock', 'sale_price', 'sale_limit'],
                instance=instance),
        }
        
class FlashsaleConditionSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=200)
    min = serializers.FloatField(default=0)
    max = serializers.FloatField(default=0)
    choice = serializers.JSONField(default=list)
    
    def validate(self, data):
        return data
    
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
        
class FlashsaleConditionDetailSerializer(FlashsaleConditionSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['type', 'min', 'max', 'choice'],
                instance=instance),
        }

class FlashsaleSerializer(serializers.Serializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    name = serializers.CharField(max_length=200)
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    
    products = FlashsaleProductSerializer(many=True)
    conditions = FlashsaleConditionSerializer(many=True)
    
    def validate(self, data):
        if self.instance: 
            return data
        
        ## validate Product integrity with Shop
        if (products := data.get('products')):
            for product in products:
                if product['product'].shop != data['shop']:
                    raise serializers.ValidationError('Product does not belong to the shop')
                data['conditions'] += [
                    {
                        'type': 'max-stock',
                        'min': 0,
                        'max': product['stock'],
                        'choice': [product['product'].id]   
                    },
                    {
                        'type': 'max-purchase',
                        'min': 0,
                        'max': product['sale_limit'],
                        'choice': [product['product'].id]
                    }
                ]
        ## validate with FlashsaleLimit
        prod_limit = FlashsaleLimit.objects.all()
        for limit in prod_limit:
            if limit.type == 'product:max-flashsale' and products:
                limitation = int(limit.value)
                for product in products:
                    if FlashsaleProduct.objects.filter(product=product['product']).count() >= limitation:
                        raise serializers.ValidationError('Product has joined too many Flashsales')
            elif limit.type == 'sale:max-period':
                limitation = {f'{limit.unit}': limit.value}
                if (data['end_date'] - data['start_date']) > timedelta(**limitation):
                    raise serializers.ValidationError('Flashsale period is over the limit')
        return data
    
    def create(self, validated_data):
        products = validated_data.pop('products', [])
        conditions = validated_data.pop('conditions', [])
        instance = Flashsale.objects.create(**validated_data)
        for product in products:
            FlashsaleProduct.objects.create(flashsale=instance, **product)
        for condition in conditions:
            FlashsaleCondition.objects.create(flashsale=instance, **condition)
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
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['name', 'start_date', 'end_date'],
                instance=instance),
            'shop': instance.shop.name,
            'products': FlashsaleProductSerializer(FlashsaleProduct.objects.filter(flashsale=instance), many=True).data,
            'conditions': FlashsaleConditionSerializer(FlashsaleCondition.objects.filter(flashsale=instance), many=True).data,
        }
    
class FlashsaleDetailSerializer(FlashsaleSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['name', 'start_date', 'end_date'],
                instance=instance),
            'shop': instance.shop.name,
            'products': FlashsaleProductSerializer(FlashsaleProduct.objects.filter(flashsale=instance), many=True).data,
            'conditions': FlashsaleConditionSerializer(FlashsaleCondition.objects.filter(flashsale=instance), many=True).data,
        }
        