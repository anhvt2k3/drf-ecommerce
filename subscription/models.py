from django.db import models
from eco_sys.mixins import SoftDeleteModelMixin

# Create your models here.
class Tier(SoftDeleteModelMixin, models.Model):
    name = models.CharField(max_length=200)
    level = models.IntegerField() # level of priority
    stripeProductID = models.CharField(max_length=200)

    description = models.TextField(default="A Tier that is available for Subscription.")
    
class Feature(SoftDeleteModelMixin, models.Model):
    name = models.CharField(max_length=200)
    path = models.CharField(max_length=200)

    description = models.TextField(default="A feature that is available for Subscription.")
    
class TierFeature(SoftDeleteModelMixin, models.Model):
    tier = models.ForeignKey(Tier, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    limitation = models.JSONField(default=dict)
    
class Plan(SoftDeleteModelMixin, models.Model):
    tier = models.ForeignKey(Tier, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    interval = models.DurationField()
    price = models.FloatField(default=0)
    stripePriceID = models.CharField(max_length=200)
    
    description = models.TextField(default="A Plan that is available for Subscription.")

class Invoice(SoftDeleteModelMixin, models.Model):
    payment = models.ForeignKey('payment.Payment', on_delete=models.CASCADE)
    subscription = models.ForeignKey('subscription.Subscription', on_delete=models.CASCADE)
    status = models.CharField(max_length=200)
    receipt = models.JSONField(default=dict)

class Subscription(SoftDeleteModelMixin, models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    tier = models.ForeignKey(Tier, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    status = models.CharField(max_length=200)
    paystatus = models.CharField(max_length=200)
    start_date = models.DateTimeField()
    expire_date = models.DateTimeField()
    stripeSubscriptionID = models.CharField(max_length=200)

    description = models.TextField(default="A Subscription that is created by User to attain Tier benefits.")
    
class Progress(SoftDeleteModelMixin, models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    isActivated = models.BooleanField(default=True)
    progression = models.JSONField(default=dict)