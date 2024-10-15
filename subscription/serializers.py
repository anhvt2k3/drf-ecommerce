import stripe
from eco_sys import secrets

from payment.models import Payment
from payment.serializers import PaymentDetailSerializer
from shop.models import Shop
from shop.serializers import ShopDetailSerializer
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers
from django.utils.timezone import datetime, timedelta

class TierSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    level = serializers.IntegerField(default=0, min_value=0)

    def create(self, validated_data):
        stripe.api_key = secrets.STRIPE_SECRET_KEY
        
        validated_data['stripeProductID'] = stripe.Product.create(
                            **{ 'name':validated_data['name'],
                                'metadata': { 'level': validated_data['level'] }
                                }).id
        return Tier.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                ['name', 'level',
                    'stripeProductID'
                ],
                instance
            )
    }

class TierDetailSerializer(TierSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                ['name', 'level', 'stripeProductID'],
                instance
            )
    }
        
class FeatureSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    model_class = serializers.CharField(max_length=200, required=False)
    path = serializers.ListField(child=serializers.CharField())
    
    def validate_model_class(self, value):
        if value:
            if not apps.get_model(value):
                raise serializers.ValidationError("Model class does not exist.")
            return value

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
                [
                    'name', 
                    # 'path'
                    ],
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
        unit_amount = int(validated_data['price']*100)
        validated_data['stripePriceID'] = stripe.Price.create(**{
            'currency': 'usd', 
            'unit_amount': unit_amount,
            'product': validated_data['tier'].stripeProductID,
            'recurring': {"interval": "day", 
                            "interval_count": validated_data['interval'].days},
                                            }).id
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
                ['name', 'price'],
                instance
            ),
            'inverval': f'{instance.interval.days} days',
            'tier_id': instance.tier.id,
            'tier': instance.tier.name
    }

class PlanDetailSerializer(PlanSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                ['name', 'price', 'stripePriceID'],
                instance
            ),
            'inverval': f'{instance.interval.days} days',
            'tier_id': instance.tier.id,
            'tier': instance.tier.name
    }

class SubscriptionSerializer(serializers.Serializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    # tier = serializers.PrimaryKeyRelatedField(queryset=Tier.objects.all())
    plan = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all())
    paymethod = serializers.PrimaryKeyRelatedField(queryset=Payment.objects.all(), required=False)
    # status = serializers.CharField(max_length=200) # start with pending
    # paystatus = serializers.CharField(max_length=200) # start with pending
    # start_date = serializers.DateTimeField() # start when payment is successful
    # expire_date = serializers.DateTimeField() # start_date + plan.interval
    
    def validate_paymethod(self, value):
        if value:
            if value.shop.merchant != self.shop.merchant:
                raise serializers.ValidationError("Payment method does not belong to user.")
            return value
        else:
            return Payment.objects.filter(user=self.shop.merchant).first()
    
    def create(self, validated_data :dict):
        stripe.api_key = secrets.STRIPE_SECRET_KEY
        
        merchant = validated_data['shop'].merchant
        #* Decide the payment method
        pm_object = Payment.objects.filter(user=merchant).first()
        decided_pm = validated_data.get('paymethod', pm_object.method_object['id'])
        
        #* Create the customer if user does not have one
        #! Only place where a stripeCustomer is created
        if not merchant.stripeCustomerID:
            customerID = merchant.stripeCustomerID = stripe.Customer.create(
                email=merchant.email
            ).id
            merchant.save()
        else: 
            customerID = merchant.stripeCustomerID
        
        #* Attach the payment method
        stripe.PaymentMethod.attach(decided_pm, customer=customerID)
        
        
        #* Fill in fields
        validated_data['tier'] = validated_data['plan'].tier
        validated_data['status'] = 'pending'
        validated_data['paystatus'] = 'pending'
        subscription = Subscription.objects.create(**validated_data)
        
        #* Create the subscription
        stripe.Subscription.create(
            customer = customerID,
            items = [{
                'price': validated_data['plan'].stripePriceID
            }],
            default_payment_method = decided_pm,
            metadata={
                'paymethod' : pm_object.id,
                'subscription' : subscription.id
            }
        )
        
        return subscription
    
    def update(self, instance, validated_data):
        instance.tier = validated_data.get('tier', instance.tier)
        instance.plan = validated_data.get('plan', instance.plan)
        instance.status = validated_data.get('status', instance.status)
        instance.paystatus = validated_data.get('paystatus', instance.paystatus)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.expire_date = validated_data.get('expire_date', instance.expire_date)
        instance.stripeSubscriptionID = validated_data.get('stripeSubscriptionID', instance.stripeSubscriptionID)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                ['status', 'paystatus', 'start_date', 'expire_date'],
                instance
            ),
            'shop_id': instance.shop.id,
            'shop': instance.shop.name,
            'owner': instance.shop.merchant.username,
            'owner_id': instance.shop.merchant.id,
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
            'shop': ShopDetailSerializer(instance.shop).data,
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
        now = datetime.now()
        feature = instance.feature
        tierfeature = instance.subscription.tier.tierfeature_set.filter(feature=feature).first()
        limit = tierfeature.limitation
        
        feature_progress = {}
        feature_progress[feature.name] = {}
        feature_progress[feature.name]['access'] = limit['access']
        
        feature_progress[feature.name]['day-usages'] = feature.feature_instance.filter(
            shop=instance.subscription.user.shop,
            created_at__date=now.date()
        ).count()
        feature_progress[feature.name]['day-cap'] = limit['day-cap']
        
        start_of_week = now - timedelta(days=now.weekday())  # Get the start of the current week (Monday)
        feature_progress[feature.name]['week-usages'] = feature.feature_instance.filter(
            shop=instance.subscription.user.shop,
            created_at__date__gte=start_of_week.date(),
            created_at__date__lte=now.date()
        ).count()
        feature_progress[feature.name]['week-cap'] = limit['week-cap']
        
        return {
            **SerializerUtils.representation_dict_formater(
                ['isActivated', 'progression'],
                instance
            ),
            'subscription_id': instance.subscription.id,
            'subscription': instance.subscription.user.username,
            'feature_id': instance.feature.id,
            'feature': instance.feature.name,
            **feature_progress
    }
        
class InvoiceSerializer(serializers.Serializer):
    payment = serializers.PrimaryKeyRelatedField(queryset=Payment.objects.all())
    subscription = serializers.PrimaryKeyRelatedField(queryset=Subscription.objects.all())
    status = serializers.CharField(max_length=200)
    receipt = serializers.JSONField()
    
    def create(self, validated_data):
        return Invoice.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.payment = validated_data.get('payment', instance.payment)
        instance.subscription = validated_data.get('subscription', instance.subscription)
        instance.status = validated_data.get('status', instance.status)
        instance.receipt = validated_data.get('receipt', instance.receipt)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                ['status'],
                instance
            ),
            'payment_id': instance.payment.id,
            'payment_stripe_id': instance.payment.method_object['id'],
            'subscription_id': instance.subscription.id,
    }
        
class InvoiceDetailSerializer(InvoiceSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                ['status', 'receipt'],
                instance
            ),
            'payment': PaymentDetailSerializer(instance.payment).data,
            'subscription': SubscriptionDetailSerializer(instance.subscription).data
    }