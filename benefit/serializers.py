from order.models import Order
from rank.models import RankConfig
from shop.models import Shop
from user.models import User
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers

class DefaultBenefitSerializer(serializers.Serializer):
    discount_type = serializers.CharField(max_length=200)
    discount_amount = serializers.FloatField(default=0)
    
    def validate_discount_amount(self, value):
        if value < 0:
            raise serializers.ValidationError('Discount amount should be a positive float.')
        return value
    
    def create(self, validated_data):
        instance_class = self
        model = DefaultBenefit
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
                input_fields=['discount_type', 'discount_amount'],
                instance=instance),
        }
        
class DefaultBenefitDetailSerializer(DefaultBenefitSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['discount_type', 'discount_amount'],
                instance=instance),
        }
        
class ConfigBenefitSerializer(serializers.Serializer):
    default_benefit = serializers.PrimaryKeyRelatedField(queryset=DefaultBenefit.objects.all())
    rank_required = serializers.PrimaryKeyRelatedField(queryset=RankConfig.objects.all())
    enabled = serializers.BooleanField(required=False)
    config_amount = serializers.FloatField(required=False,min_value=0)
    
    def validate_config_amount(self, value):
        if value < 0:
            raise serializers.ValidationError('Config amount should be a positive float.')
        return value
    
    def create(self, validated_data):
        if not validated_data.get('config_amount'):
            validated_data['config_amount'] = validated_data['default_benefit'].discount_amount
        
        instance_class = self
        model = ConfigBenefit
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
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['enabled', 'config_amount'],
                instance=instance),
            'benefit_type': instance.default_benefit.discount_type,
            'rank_required': instance.rank_required.rank.name,
            'shop_name': instance.rank_required.shop.name,
            'shop_id': instance.rank_required.shop.id,
        }

class ConfigBenefitDetailSerializer(ConfigBenefitSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['enabled', 'config_amount'],
                instance=instance),
            'benefit_type': instance.default_benefit.discount_type,
            'rank_required': instance.rank_required.rank.name,
            'shop_name': instance.rank_required.shop.name,
            'shop_id': instance.rank_required.shop.id,
        }
        
class UserBenefitSerializer(serializers.Serializer):
    benefit = serializers.PrimaryKeyRelatedField(queryset=ConfigBenefit.objects.all())
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all(), required=False)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    is_activate = serializers.BooleanField(default=True)
    
    def create(self, validated_data):
        validated_data['shop'] = validated_data['benefit'].rank_required.shop
        instance_class = self
        model = UserBenefit
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
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['is_activate'],
                instance=instance),
            'user': instance.user.username,
            'shop': instance.shop.name,
            'required rank': instance.benefit.rank_required.rank.name,
            'benefit_type': instance.benefit.default_benefit.discount_type,
            'benefit': instance.benefit.config_amount,
            'benefit_id': instance.benefit.id,
        }
        
class UserBenefitDetailSerializer(UserBenefitSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['is_activate'],
                instance=instance),
            'user': instance.user.username,
            'shop': instance.shop.name,
            'required rank': instance.benefit.rank_required.rank.name,
            'benefit_type': instance.benefit.default_benefit.discount_type,
            'benefit': instance.benefit.config_amount,
            'benefit_id': instance.benefit.id,
        }