import stripe

from payment.models import Payment
from user.models import User
from ..eco_sys import secrets
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers

class TierSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    level = serializers.IntegerField()

    def create(self, validated_data):
        stripe.api_key = secrets.STRIPE_SECRET_KEY
        
        validated_data['stripeProductID'] = stripe.Product.create(
                            **{ 'name':validated_data['name'],
                                'metadata': { 'level': validated_data['level'] }
                                })
        return Tier.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.price = validated_data.get('price', instance.price)
        instance.period = validated_data.get('period', instance.period)
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
                ['limitation'],
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
            'tier': TierDetailSerializer(instance.tier).data,
            'feature': FeatureDetailSerializer(instance.feature).data
    }
        
class PlanSerializer(serializers.Serializer):
    tier = serializers.PrimaryKeyRelatedField(queryset=Tier.objects.all())
    name = serializers.CharField(max_length=200)
    interval = serializers.DurationField() # must be in days
    price = serializers.FloatField()
    
    def create(self, validated_data):
        stripe.api_key = secrets.STRIPE_SECRET_KEY
        validated_data['stripePriceID'] = stripe.Price.create(**{
            'product': validated_data['tier'].stripeProductID,
            'recurring': {"interval": "day", "interval_count": validated_data['interval'].days},
                                            })
        return Plan.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.tier = validated_data.get('tier', instance.tier)
        instance.name = validated_data.get('name', instance.name)
        instance.interval = validated_data.get('interval', instance.interval)
        instance.price = validated_data.get('price', instance.price)
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
                ['name', 'interval', 'price', 'charge', 'stripePriceID'],
                instance
            ),
            'tier_id': instance.tier.id,
            'tier': instance.tier.name
    }

class SubscriptionSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    # tier = serializers.PrimaryKeyRelatedField(queryset=Tier.objects.all())
    plan = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all())
    paymethod = serializers.PrimaryKeyRelatedField(queryset=Payment.objects.all(), required=False)
    # status = serializers.CharField(max_length=200) # start with pending
    # paystatus = serializers.CharField(max_length=200) # start with pending
    # start_date = serializers.DateTimeField() # start when payment is successful
    # expire_date = serializers.DateTimeField() # start_date + plan.interval
    
    def validate_paymethod(self, value):
        if value:
            if value.user != self.user:
                raise serializers.ValidationError("Payment method does not belong to user.")
            return value
        else:
            return Payment.objects.filter(user=self.user).first()
    
    def create(self, validated_data):
        stripe.api_key = secrets.STRIPE_SECRET_KEY
        #* Create the customer if user does not have one
        #! This is the only place where a Customer is created
        if not validated_data['user'].stripeCustomerID:
            customerID = validated_data['user'].stripeCustomerID = stripe.Customer.create(
                email=validated_data['user'].email
            )
            validated_data['user'].save()
        else:
            customerID = validated_data['user'].stripeCustomerID
        #* Create the subscription
        validated_data['stripeSubscriptionID'] = stripe.Subscription.create(**{
            'customer': customerID,
            'items': [{
                'price': validated_data['plan'].stripePriceID
            }],
            'default_payment_method': Payment.objects.filter(user=validated_data['user']).first().method_object['id']
        })
        #* Fill in fields
        validated_data['tier'] = validated_data['plan'].tier
        validated_data['status'] = 'pending'
        validated_data['paystatus'] = 'pending'
        return Subscription.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.user = validated_data.get('user', instance.user)
        instance.tier = validated_data.get('tier', instance.tier)
        instance.plan = validated_data.get('plan', instance.plan)
        instance.status = validated_data.get('status', instance.status)
        instance.paystatus = validated_data.get('paystatus', instance.paystatus)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.expire_date = validated_data.get('expire_date', instance.expire_date)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                ['status', 'paystatus', 'start_date', 'expire_date'],
                instance
            ),
            'user_id': instance.user.id,
            'user': instance.user.username,
            'tier_id': instance.tier.id,
            'tier': instance.tier.name,
            'plan_id': instance.plan.id,
            'plan': instance.plan.name
    }
        
class SubscriptionDetailSerializer(SubscriptionSerializer):
    def to_representation(self, instance):
        from user.serializers import UserDetailSerializer
        return {
            **SerializerUtils.detail_dict_formater(
                ['status', 'paystatus', 'start_date', 'expire_date', 'stripeSubscriptionID'],
                instance
            ),
            'user': UserDetailSerializer(instance.user).data,
            'tier': TierDetailSerializer(instance.tier).data,
            'plan': PlanDetailSerializer(instance.plan).data,
            'progress': ProgressSerializer(instance.progress_set, many=True).data
    }
        
class ProgressSerializer(serializers.Serializer):
    subscription = serializers.PrimaryKeyRelatedField(queryset=Subscription.objects.all())
    feature = serializers.PrimaryKeyRelatedField(queryset=Feature.objects.all())
    isActivated = serializers.BooleanField()
    progression = serializers.JSONField()
    
    def create(self, validated_data):
        return Progress.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.subscription = validated_data.get('subscription', instance.subscription)
        instance.feature = validated_data.get('feature', instance.feature)
        instance.isActivated = validated_data.get('isActivated', instance.isActivated)
        instance.progression = validated_data.get('progression', instance.progression)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                ['isActivated', 'progression'],
                instance
            ),
            'subscription_id': instance.subscription.id,
            'subscription': instance.subscription.user.username,
            'feature_id': instance.feature.id,
            'feature': instance.feature.name
    }