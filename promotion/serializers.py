from benefit.models import DefaultBenefit
from notification.models import Notification
from notification.serializers import NotificationSerializer
from shop.models import Shop
from shop.serializers import ShopDetailSerializer, ShopSerializer
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers


class DefaultPromotionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    benefit_type = serializers.CharField(max_length=200)
    benefit_value = serializers.CharField(default=0)
    #! non-model fields
    conditions = serializers.JSONField()
    
    def validate(self, attrs):
        if not self.instance:
            promocondseri = PromoConditionSerializer(data=attrs['conditions'],many=True)
            if not promocondseri.is_valid():
                raise serializers.ValidationError(promocondseri.errors)
            attrs['conditions'] = promocondseri.validated_data
        return attrs
    
    def create(self, validated_data):
        conditions = validated_data.pop('conditions')
        
        instance_class = self
        model = DefaultPromotion
        validated_data = validated_data
        #! Create instance with required fields from Serialier class.
        fields = validated_data.keys()
        args = {}
        for field in fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()
        
        PromoCondition.objects.bulk_create([PromoCondition(**{**item, 'defaultPromo': instance}) for item in conditions])
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
                input_fields=['name','benefit_type', 'benefit_value'],
                instance=instance),
            'conditions': [{
                            'type':item.cond_type,
                            'choice': item.cond_choice if item.cond_choice else [],
                            'min':item.cond_min} for item in instance.promocondition_set.all()]
        }
class DefaultPromotionDetailSerializer(DefaultPromotionSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['name','benefit_type', 'benefit_value'],
                instance=instance),
            'conditions': [PromoConditionDetailSerializer(item).data for item in instance.promocondition_set.all()]
        }
class PromotionSerializer(serializers.Serializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    
    name = serializers.CharField(max_length=200, required=False)
    start_date = serializers.DateTimeField(default=timezone.now)
    end_date = serializers.DateTimeField(default=timezone.now() + timedelta(days=1))
    benefit_type = serializers.CharField(max_length=200, required=False)
    benefit_value = serializers.CharField(required=False)
    #! non-model fields
    defaultPromo = serializers.PrimaryKeyRelatedField(queryset=DefaultPromotion.objects.all(), required=False)
    conditions = serializers.JSONField(required=False)
    
    # notify_buyers = serializers.BooleanField(default=False)
    notification = serializers.JSONField(default=dict, required=False)
    
    def validate(self, data):
        if not self.instance:
            #! Check if defaultPromo or full Promotion infos are provided.
            if 'defaultPromo' not in data and ['name', 'benefit_type', 'benefit_value','conditions'] not in data:
                raise serializers.ValidationError("DefaultPromotion or full Promotion infos must be provided.")
            #! Validate conditions
            promocondseri = PromoConditionSerializer(data=data['conditions'],many=True)
            if not promocondseri.is_valid():
                raise serializers.ValidationError(promocondseri.errors)
            data['conditions'] = promocondseri.validated_data
            #! Validate notification
            notification = data.pop('notification', {})
            notifications = [{
                'recipient': item.user.id,
                'shop': data['shop'].id,
                'type': 'promotion-announcement',
                'title': notification.get("title", f'New Promotion {data["name"]} from {data["shop"].name}'),
                'message': notification.get("message", f'New Promotion {data["name"]} from {data["shop"].name} is available now!'),
                'priority': notification.get("priority", 0),
                        } for item in data['shop'].buyer_set.all()]
            if not (notiseri := NotificationSerializer(data=notifications, many=True)).is_valid():
                raise serializers.ValidationError(notiseri.errors)
            data['notification'] = notiseri.validated_data
        return data
    
    def create(self, validated_data):
        if (defaultpromo := validated_data.pop('defaultPromo')):
            if 'name' not in validated_data: validated_data['name'] = defaultpromo.name
            if 'benefit_type' not in validated_data: validated_data['benefit_type'] = defaultpromo.benefit_type 
            if 'benefit_value' not in validated_data: validated_data['benefit_value'] = str(defaultpromo.benefit_value)
            if 'conditions' not in validated_data: 
                validated_data['conditions'] = [{ 
                    'cond_type': item.cond_type,
                    'cond_choice': item.cond_choice,
                    'cond_min': item.cond_min,
                    'cond_max': item.cond_max}
                    for item in defaultpromo.promocondition_set.all()]
        conditions = validated_data.pop('conditions')
        notifications = validated_data.pop('notification')
        
        instance_class = self
        model = Promotion
        validated_data = validated_data
        #! Create instance with required fields from Serialier class.
        fields = validated_data.keys()
        args = {}
        for field in fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()
        #! Create conditions
        PromoCondition.objects.bulk_create([PromoCondition(**{**item, 'promotion': instance}) for item in conditions])
        #! Create notifications
        Notification.objects.bulk_create([
            Notification(item) for item in notifications 
                if True and item.update({'link': f'http://localhost:8000/promo/me/{instance.id}','additional_data': {'promotion': instance.id}})
                ])
        
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
        [PromoConditionSerializer(item).delete() for item in instance.promocondition_set.all()]
        notifications = [{
            'recipient': item.user.id,
            'shop': instance.shop.id,
            'type': 'promotion-deletion',
            'title': f'Promotion {instance.name} is overdue',
            'message': f'Promotion {instance.name} has just been overdue! Thank you for particapating.',
            'link': f'http://localhost:8000/promo/me/{instance.id}',
            'read_status': False,
            'priority': 0,
            'additional_data': {'promotion': instance.id}
            } for item in instance.shop.buyer_set.all()]
        notiseri = NotificationSerializer(data=notifications, many=True)
        try:
            if notiseri.is_valid(raise_exception=True):
                notiseri.save()
        except Exception as e:
            raise e
        instance.delete()
        return instance
    
    def to_representation(self, instance):
        return {
            'shop': instance.shop.name,
            **SerializerUtils.representation_dict_formater(
                input_fields=['name','benefit_type', 'benefit_value', 'start_date', 'end_date'],
                instance=instance),
            'conditions': [{
                            'type':item.cond_type,
                            'choice': item.cond_choice,
                            'min':item.cond_min,
                            'max':item.cond_max} for item in instance.promocondition_set.all()]
        }
        
class PromotionDetailSerializer(PromotionSerializer):
    def to_representation(self, instance):
        return {
            'shop': ShopDetailSerializer(instance.shop).data,
            **SerializerUtils.detail_dict_formater(
                input_fields=['benefit_type', 'benefit_value', 'start_date', 'end_date'],
                instance=instance),
            'conditions': [PromoConditionDetailSerializer(item).data for item in instance.promocondition_set.all()]
        }
        
class PromoConditionSerializer(serializers.Serializer):
    
    promotion = serializers.PrimaryKeyRelatedField(queryset=Promotion.objects.all(), required=False)
    defaultPromo = serializers.PrimaryKeyRelatedField(queryset=DefaultPromotion.objects.all(), required=False) 
    
    cond_type = serializers.CharField(max_length=200)
    cond_choice = serializers.JSONField(default=list)
    cond_min = serializers.FloatField(default=0)
    cond_max = serializers.FloatField(default=0)
    """
        cond_type = 'product_range' -> cond_choices = [1,2,3,4,5]
        cond_type = 'charge' -> cond_min = 100
        cond_type = 'quantity' -> cond_min = 1
        cond_type = 'rank' -> cond_choices = ['Bronze', 'Silver', 'Gold', 'Platinum']
        cond_type = 'item_charge' -> cond_min = 10
        cond_type = 'item_quantity' -> cond_min = 1
    """
    def validate(self, data):
        # if 'promotion' not in data and 'defaultPromo' not in data:
        #     raise serializers.ValidationError("Promotion or DefaultPromotion must be provided.")
        if 'promotion' in data and 'defaultPromo' in data:
            raise serializers.ValidationError("Promotion and DefaultPromotion cannot be provided together.")
        return data
        
    def create(self, validated_data):
        instance_class = self
        model = PromoCondition
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
            'promotion': instance.promotion.name or instance.defaultPromo.name,
            'promotion_id': instance.promotion.id or instance.defaultPromo.id,
            'is_default': instance.defaultPromo is not None,
            **SerializerUtils.representation_dict_formater(
                input_fields=['cond_type', 'cond_choice', 'cond_min', 'cond_max'],
                instance=instance),
        }

class PromoConditionDetailSerializer(PromoConditionSerializer):
    def to_representation(self, instance):
        return {
            'promotion': PromotionDetailSerializer(instance.promotion).data if instance.promotion else DefaultPromotionDetailSerializer(instance.defaultPromo).data,
            'is_default': instance.defaultPromo is not None,
            **SerializerUtils.detail_dict_formater(
                input_fields=['cond_type', 'cond_choice', 'cond_min'],
                instance=instance),
        }