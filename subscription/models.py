from django.db import models
from django.apps import apps
from eco_sys.mixins import BasicManager, SoftDeleteModelMixin

# Create your models here.

class Tier(SoftDeleteModelMixin, models.Model):
    name = models.CharField(max_length=200)
    level = models.IntegerField() # level of priority
    stripeProductID = models.CharField(max_length=200)

    description = models.TextField(default="A Tier that is available for Subscription.")
    
class Feature(SoftDeleteModelMixin, models.Model):
    name = models.CharField(max_length=200)
    model_class = models.CharField(max_length=200, default="") # Model class name
    path = models.JSONField(default=list)
    
    @property
    def feature_instance(self):
        return apps.get_model(self.model_class)

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
    
class SubscriptionActiveManager(BasicManager):
    def get_queryset(self):
        from django.utils import timezone
        return super().get_queryset().filter(status='active', expire_date__gte=timezone.now())
#@ Alternative approach
# class SubscriptionActiveManager(SoftDeleteModelMixin.objects.__class__):
#     def onDutyGetter(self, shop):
#         from django.utils import timezone
#         return Subscription.objects.filter(shop=shop, status='active', expire_date__gte=timezone.now()).first()
# ...
# ...
    # objects = SubscriptionActiveManager()
class Subscription(SoftDeleteModelMixin, models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    tier = models.ForeignKey(Tier, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    status = models.CharField(max_length=200)
    paystatus = models.CharField(max_length=200)
    start_date = models.DateTimeField(null=True, blank=True)
    expire_date = models.DateTimeField(null=True, blank=True)
    stripeSubscriptionID = models.CharField(max_length=200, null=True, blank=True)

    description = models.TextField(default="A Subscription that is created by User to attain Tier benefits.")
    
    onDuties = SubscriptionActiveManager()
    
class Progress(SoftDeleteModelMixin, models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    isActivated = models.BooleanField(default=True)
    progression = models.JSONField(default=dict)