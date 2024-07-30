from benefit.models import ConfigBenefit, DefaultBenefit
from benefit.serializers import ConfigBenefitSerializer, DefaultBenefitSerializer
from shop.models import Shop
from user.models import User
from .models import *
from .utils.utils import *

class DefaultCouponSerializer(serializers.Serializer):
    benefit_set = serializers.PrimaryKeyRelatedField(queryset=DefaultBenefit.objects.all(), many=True)
    exchange_point = serializers.IntegerField(required=False)
    usage_limit = serializers.IntegerField(required=False)
    #* input = list[id] // output = list[object]
    
    def create(self, validated_data):
        benefit_set = validated_data.pop('benefit_set')
        
        instance_class = self
        model = DefaultCoupon
        validated_data = validated_data
        #! Create instance with required fields from Serialier class.
        fields = validated_data.keys()
        args = {}
        for field in fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.benefit_set.set(benefit_set)
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
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['exchange_point', 'usage_limit'],
                instance=instance),
            'benefit_set': [DefaultBenefitSerializer(item).data for item in instance.benefit_set.all()],
            }
        
class DefaultCouponDetailSerializer(DefaultCouponSerializer):
    def to_representation(self, instance):
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['exchange_point', 'usage_limit'],
                instance=instance),
            'benefit_set': [DefaultBenefitSerializer(item).data for item in instance.benefit_set.all()],
            }
    
class CouponSerializer(serializers.Serializer):
    default = serializers.PrimaryKeyRelatedField(queryset=DefaultCoupon.objects.all())
    benefit_set = serializers.PrimaryKeyRelatedField(queryset=ConfigBenefit.objects.all(), many=True, required=False)
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    exchange_point = serializers.IntegerField(required=False)
    usage_limit = serializers.IntegerField(required=False)
    
    def create(self, validated_data):
        if 'exchange_point' not in validated_data:
            validated_data['exchange_point'] = validated_data['default'].exchange_point
        if 'usage_limit' not in validated_data:
            validated_data['usage_limit'] = validated_data['default'].usage_limit
        if 'benefit_set' not in validated_data:
            try:
                largest_discount_amount_configbenefit_per_coupon_default_benefit = [ConfigBenefit.objects.filter(default_benefit=item).order_by('-config_amount').first().id for item in validated_data['default'].benefit_set.all()]
            except AttributeError as e:
                raise serializers.ValidationError(f'One or more default Benefit is not created with a Config Benefit.')
            validated_data['benefit_set'] = ConfigBenefit.objects.filter(
                                                    rank_required__shop=validated_data['shop'], 
                                                    enabled=True,
                                                    id__in=largest_discount_amount_configbenefit_per_coupon_default_benefit)
        benefit_set = validated_data.pop('benefit_set')
        
        instance_class = self
        model = Coupon
        validated_data = validated_data
        #! Create instance with required fields from Serialier class.
        fields = validated_data.keys()
        args = {}
        for field in fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.benefit_set.set(benefit_set)
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
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['exchange_point', 'usage_limit'],
                instance=instance),
            'shop': instance.shop.name,
            'default': instance.default.id,
            'benefit_set': [{ 
                            'id': item.id,
                            'discount_type': item.default_benefit.discount_type,
                            'config_amount': item.config_amount,
                            'enabled': item.enabled,
                                    } 
                            for item in instance.benefit_set.all()],
            }

class CouponDetailSerializer(CouponSerializer):
    def to_representation(self, instance):
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['exchange_point', 'usage_limit'],
                instance=instance),
            'shop': instance.shop.name,
            'default': instance.default.id,
            'benefit_set': [{ 
                            'id': item.id,
                            'discount_type': item.default_benefit.discount_type,
                            'config_amount': item.config_amount,
                            'enabled': item.enabled,
                                    } 
                            for item in instance.benefit_set.all()],
            }