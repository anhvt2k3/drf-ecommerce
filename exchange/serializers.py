from coupon.models import Coupon
from coupon.serializers import CouponSerializer
from shop.models import Buyer, Shop
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers

class PointExchangeSerializer(serializers.Serializer):
    buyer = serializers.PrimaryKeyRelatedField(queryset=Buyer.objects.all())
    coupon = serializers.PrimaryKeyRelatedField(queryset=Coupon.objects.all())
    
    def validate(self, data):
        if not self.instance:
            buyer = data['buyer']
            coupon = data['coupon']
            ## check if user has enough point to exchange this coupon
            remain_point = buyer.total_point - PointExchange.objects.used_point(buyer)
            if remain_point < coupon.exchange_point:
                raise serializers.ValidationError('User dont have enough point to exchange this coupon.')
            data['remain_usage'] = data['coupon'].usage_limit
            ## check if user has already exchanged this coupon
            if  PointExchange.objects.filter(buyer=buyer, coupon=coupon).exists():
                raise serializers.ValidationError('User has already exchanged for this coupon.')       
        return data
    
    def create(self, validated_data):
        instance_class = self
        model = PointExchange
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
        #@ this should never be true
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=[],
                instance=instance),
            'buyer': instance.buyer.user.username,
            'buyer_id': instance.buyer.id,
            'coupon': {
                'id': instance.coupon.id,
                'exchange_point': instance.coupon.exchange_point,
                'usage_limit': instance.coupon.usage_limit,
                },
            'shop': instance.coupon.shop.name,
            'remain_usage': instance.remain_usage,
        }

class PointExchangeDetailSerializer(PointExchangeSerializer):
    def to_representation(self, instance):
        #@ this should never be true
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=[],
                instance=instance),
            'buyer': instance.buyer.user.username,
            'buyer_id': instance.buyer.id,
            'coupon': {
                'id': instance.coupon.id,
                'exchange_point': instance.coupon.exchange_point,
                'usage_limit': instance.coupon.usage_limit,
                },
            'shop': instance.coupon.shop.name,
            'remain_usage': instance.remain_usage,
        }
        