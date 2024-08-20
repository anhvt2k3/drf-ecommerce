from benefit.serializers import UserBenefitSerializer
from exchange.models import PointExchange
from exchange.serializers import PointExchangeSerializer
from quest.models import Quest
from rank.models import Rank, RankConfig
from rank.serializers import RankConfigSerializer
from user.models import User
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers

class ShopSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    merchant = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    def validate_name(self, value):
        if Shop.objects.filter(name=value).exists():
            raise serializers.ValidationError('Shop with this name already exists. Choose another name.')
        return value
    
    def validate_merchant(self, value):
        if not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError('User with this id does not exists.')
        # if self.instance.merchant:
        #     raise serializers.ValidationError('Merchant is not allowed to be changed.')
        merchant = User.objects.filter(id=value.id, is_merchant=True)
        if merchant.exists():
            shop = Shop.objects.filter(merchant=merchant.first()).first()
            raise serializers.ValidationError(f'This User has already owned a Shop: {shop.name}')
        return value
    
    def create(self, validated_data):
        merchant = User.objects.filter(id=validated_data['merchant'].id).first()
        merchant.is_merchant = True
        merchant.save()
        
        instance_class = self
        model = Shop
        validated_data = validated_data
        #! Create instance with required fields from Serialier class.
        fields = validated_data.keys()
        args = {}
        for field in fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()
        
        guest_rank = Rank.objects.filter(required_point=0).first()
        if not guest_rank:
            raise serializers.ValidationError('No default Rank is created for Guest! Please issue Admin of this problem.')
        rank_seri = RankConfigSerializer(data={'rank':6, 'shop':instance.id})
        if not rank_seri.is_valid():
            self.delete()
            raise serializers.ValidationError(f'Default RankConfig for this Shop created failed: {rank_seri.errors}')
        
        rank_seri.save()
        return instance
    
    def update(self, instance :models.Model, validated_data :dict):
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
        instance.merchant.is_merchant = False
        instance.merchant.save()
        instance.delete()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['name'],
                instance=instance),
            'merchant': instance.merchant.username,
            'merchant_id': instance.merchant.id
        }
        
class ShopDetailSerializer(ShopSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['name'],
                instance=instance),
            'merchant': instance.merchant.username,
            'merchant_id': instance.merchant.id
        }

class BuyerSerializer(serializers.Serializer):
    """
{ 
    "user": 1, "shop": 1 
}
    """        
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    rank = serializers.PrimaryKeyRelatedField(queryset=RankConfig.objects.all(), required=False)
    total_point = serializers.IntegerField(default=0)
    
    def create(self, validated_data):
        validated_data['rank'] = RankConfig.objects.filter(shop=validated_data['shop'].id, is_default=True).first()
        
        instance_class = self
        model = Buyer
        validated_data = validated_data
        #! Create instance with required fields from Serialier class.
        fields = validated_data.keys()
        args = {}
        for field in fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()
        return instance
    
    def update(self, instance :models.Model, validated_data :dict):
        instance = instance
        validated_data = validated_data
        exclude_fields = ['id', 'shop', 'user']
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
        from order.serializers import OrderForceDeleteSerializer
        from django.db import transaction
        with transaction.atomic():
            [PointGainSerializer(point_gain).delete() for point_gain in instance.pointgain_set.all()]
            [UserBenefitSerializer(userbenefit).delete() for userbenefit in instance.user.userbenefit_set.filter(benefit__rank_required__shop=instance.shop)]
            [OrderForceDeleteSerializer(order).delete() for order in instance.user.order_set.filter(orderitem__product__shop=instance.shop)]
            [PointExchangeSerializer(point_exchange).delete() for point_exchange in instance.pointexchange_set.filter(buyer=instance)]
            instance.delete()
        return instance
    
    def to_representation(self, instance):
        next_rank = instance.shop.rankconfig_set.filter(required_point__gt=instance.total_point).order_by('required_point').first()
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['total_point'],
                instance=instance),
            'remain_point': instance.total_point - PointExchange.objects.used_point(instance.id),
            'shop': instance.shop.name,
            'shop_id': instance.shop.id,
            'rank': instance.rank.rank.name,
            'next_rank': next_rank.rank.name if next_rank else None,
            'next_rank_point': next_rank.required_point if next_rank else None,
            'user': instance.user.username,
            'user_id': instance.user.id,
        }
        
class BuyerDetailSerializer(BuyerSerializer):
    def to_representation(self, instance):
        next_rank = instance.shop.rankconfig_set.filter(required_point__gt=instance.total_point).order_by('required_point').first()
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['total_point'],
                instance=instance),
            'remain_point': instance.total_point - PointExchange.objects.used_point(instance.id),
            'shop': instance.shop.name,
            'shop_id': instance.shop.id,
            'rank': instance.rank.rank.name,
            'next_rank': next_rank.rank.name if next_rank else None,
            'next_rank_point': next_rank.required_point if next_rank else None,
            'user': instance.user.username,
            'user_id': instance.user.id,
        }
        
class PointGainSerializer(serializers.Serializer):
    buyer = serializers.PrimaryKeyRelatedField(queryset=Buyer.objects.all())
    quest = serializers.PrimaryKeyRelatedField(queryset=Quest.objects.all())
    current_rank = serializers.CharField(max_length=100)
    gain_point = serializers.IntegerField(default=0)
    
    def create(self, validated_data):
        instance_class = self
        model = PointGain
        validated_data = validated_data
        #! Create instance with required fields from Serialier class.
        fields = validated_data.keys()
        args = {}
        for field in fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()
        
        progress_spend = ProgressSerializer(data={'point_gain': instance.id, 'prog_type':'spending', 'goal_value': instance.quest.min_spent})
        if not progress_spend.is_valid():
            instance.delete()
            raise serializers.ValidationError(f'Progress creation failed: {progress_spend.errors}')
        progress_spend.save()
        progress_quantity = ProgressSerializer(data={'point_gain': instance.id, 'prog_type':'quantity', 'goal_value': instance.quest.min_quantity})
        if not progress_quantity.is_valid():
            progress_spend.delete()
            instance.delete()
            raise serializers.ValidationError(f'Progress creation failed: {progress_quantity.errors}')
        progress_quantity.save()
        
        return instance
    
    def update(self, instance :models.Model, validated_data :dict):
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
        [ProgressSerializer(progress).delete() for progress in instance.progress_set.all()]
        instance.delete()
        return instance
    
    def to_representation(self, instance : PointGain):
        from order.models import OrderItem
        from order.serializers import OrderItemSerializer
        # print ('pointgain.progress',[field.name for field in instance._meta.get_fields()])
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['gain_point', 'current_rank'],
                instance=instance),
            'quest': instance.quest.name,
            'quest_id': instance.quest.id,
            'buyer': instance.buyer.user.username,
            'buyer_id': instance.buyer.id,
            'shop': instance.buyer.shop.name,
            'shop_id': instance.buyer.shop.id,
            'spend_progress': f"{instance.progress_set.filter(prog_type='spending').first().progression} / {instance.quest.min_spent}",
            'quantity_progress': f"{instance.progress_set.filter(prog_type='quantity').first().progression} / {instance.quest.min_quantity}",
            'orderitems': [{
                    'id': orderitem.id,
                    'order': orderitem.order.id,
                    'total_charge': orderitem.product.price * orderitem.quantity,
                    'quantity': orderitem.quantity,
                    'product': orderitem.product.id,
                }
                for orderitem in OrderItem.objects.filter(id__in=instance.orderitems)]
        } 
        
class PointGainDetailSerializer(PointGainSerializer):
    def to_representation(self, instance : PointGain):
        from order.models import OrderItem
        from order.serializers import OrderItemSerializer
        # print ('pointgain.progress',[field.name for field in instance._meta.get_fields()])
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['gain_point', 'current_rank'],
                instance=instance),
            'quest': instance.quest.name,
            'quest_id': instance.quest.id,
            'buyer': instance.buyer.user.username,
            'buyer_id': instance.buyer.id,
            'shop': instance.buyer.shop.name,
            'shop_id': instance.buyer.shop.id,
            'spend_progress': f"{instance.progress_set.filter(prog_type='spending').first().progression} / {instance.quest.min_spent}",
            'quantity_progress': f"{instance.progress_set.filter(prog_type='quantity').first().progression} / {instance.quest.min_quantity}",
            'orderitems': [{
                    'id': orderitem.id,
                    'order': orderitem.order.id,
                    'total_charge': orderitem.total_charge,
                    'quantity': orderitem.quantity,
                    'product': orderitem.product.id,
                }
                for orderitem in OrderItem.objects.filter(id__in=instance.orderitems)]
        } 
        
class ProgressSerializer(serializers.Serializer):
    point_gain = serializers.PrimaryKeyRelatedField(queryset=PointGain.objects.all())
    prog_type = serializers.CharField(max_length=100)
    goal_value = serializers.FloatField()
    progression = serializers.FloatField(default=0)
    
    def create(self, validated_data):
        if Progress.objects.filter(point_gain=validated_data['point_gain'].id, prog_type=validated_data['prog_type']).exists():
            raise serializers.ValidationError('Progress with this type already exists.')
        
        instance_class = self
        model = Progress
        validated_data = validated_data
        #! Create instance with required fields from Serialier class.
        fields = validated_data.keys()
        args = {}
        for field in fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()
        return instance
    
    def update(self, instance :models.Model, validated_data :dict):
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
                input_fields=['goal_value', 'progression', 'prog_type'],
                instance=instance),
        } 
        
class ProgressDetailSerializer(ProgressSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['goal_value', 'progression', 'prog_type'],
                instance=instance),
        } 