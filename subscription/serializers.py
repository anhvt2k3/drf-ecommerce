from user.models import User
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers

class TierSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    price = serializers.FloatField()
    period = serializers.DurationField()
    stripeProductID = serializers.CharField(max_length=200, required=False)

    def create(self, validated_data):
        return Tier.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.price = validated_data.get('price', instance.price)
        instance.period = validated_data.get('period', instance.period)
        instance.stripeProductID = validated_data.get('stripeProductID', instance.stripeProductID)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                ['name', 'price', 'period'],
                instance
            )
    }

class TierDetailSerializer(TierSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                ['name', 'price', 'period', 'stripeProductID'],
                instance
            )
    }
        
class FeatureSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    path = serializers.CharField(max_length=200)
    
    def create(self, validated_data):
        return Feature.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.path = validated_data.get('path', instance.path)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                ['name', 'path'],
                instance
            )
    }
        
class FeatureDetailSerializer(FeatureSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                ['name', 'path'],
                instance
            )
    }
        
class TierFeatureSerializer(serializers.Serializer):
    tier = serializers.PrimaryKeyRelatedField(queryset=Tier.objects.all())
    feature = serializers.PrimaryKeyRelatedField(queryset=Feature.objects.all())
    limitation = serializers.JSONField()
    
    def create(self, validated_data):
        return TierFeature.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.tier = validated_data.get('tier', instance.tier)
        instance.feature = validated_data.get('feature', instance.feature)
        instance.limitation = validated_data.get('limitation', instance.limitation)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                [],
                instance
            ),
            'tier_id': instance.tier.id,
            'tier': instance.tier.name,
            'feature_id': instance.feature.id,
            'feature': instance.feature.name
    }
        
class TierFeatureDetailSerializer(TierFeatureSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                ['limitation'],
                instance
            ),
            'tier_id': instance.tier.id,
            'tier': instance.tier.name,
            'feature_id': instance.feature.id,
            'feature': instance.feature.name
    }
        
class PlanSerializer(serializers.Serializer):
    tier = serializers.PrimaryKeyRelatedField(queryset=Tier.objects.all())
    name = serializers.CharField(max_length=200)
    interval = serializers.DurationField()
    price = serializers.FloatField()
    charge = serializers.FloatField()
    
    def create(self, validated_data):
        return Plan.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.tier = validated_data.get('tier', instance.tier)
        instance.name = validated_data.get('name', instance.name)
        instance.interval = validated_data.get('interval', instance.interval)
        instance.price = validated_data.get('price', instance.price)
        instance.charge = validated_data.get('charge', instance.charge)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                ['name', 'interval', 'price', 'charge'],
                instance
            ),
            'tier_id': instance.tier.id,
            'tier': instance.tier.name
    }

class PlanDetailSerializer(PlanSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                ['name', 'interval', 'price', 'charge'],
                instance
            ),
            'tier_id': instance.tier.id,
            'tier': instance.tier.name
    }
