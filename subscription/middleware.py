from django.http import HttpResponseForbidden
from requests import Response

from subscription.models import Feature, TierFeature

class FeatureAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Example of getting the user's tier and the feature they're accessing
        tier = request.user.subscription.tier
        if not (feature := self.get_feature_from_request(request)): return self.get_response(request)
        feature_limits = TierFeature.objects.filter(tier=tier, feature=feature).values('limitation').first()
        progression = request.user.subscription.progress_set.filter(feature=feature).first().progression
        
        if not (forbidResponse := self.limitNprogression_reconcile(
                                    feature_limits=feature_limits,
                                    progression=progression,
                                    shop=request.user.shop,
                                    feature=feature
                                        )):
            return forbidResponse
            
        # Proceed with the request
        return self.get_response(request)

    def get_feature_from_request(self, request):
        # Extract the feature based on the request path, e.g., from the URL
        fpath = request.path
        if 'my' not in fpath:
            return None
        return Feature.objects.filter(path__in=[fpath]).first()
    
    def limitNprogression_reconcile(self, feature_limits, progression, shop, feature: Feature):
        # Check if the user has reached the limit for the feature
        from django.utils.timezone import datetime, timedelta
        
        for f, v in feature_limits.items():
            if progression.get(f, 0) >= v:
                return Response(status=403, data=f"Feature limit reached for {feature.name} !")
            elif f is 'day-cap':
                now = datetime.now()
                
                today_instances = feature.feature_instance.filter(
                    shop=shop, 
                    created_at__date=now.date()
                ).count()
                
                if today_instances >= v:
                    return Response(status=403, data=f"Feature limit reached for {feature.name} for today !")
            elif f is 'week-cap':
                now = datetime.now()
                start_of_week = now - timedelta(days=now.weekday())  # Get the start of the current week (Monday)
                
                week_instances = feature.feature_instance.filter(
                    shop=shop,
                    created_at__date__gte=start_of_week.date(),
                    created_at__date__lte=now.date()
                ).count()
                
                if week_instances >= v:
                    return Response(status=403, data=f"Feature limit reached for {feature.name} for this week !")
        
        return None
        

    
"""
-- Feature recommend objects list
[
    {
        'name': 'Flashsale',
        'model_class': 'flashsale.Flashsale',
        'path': ['flashsales']
    },
    {
        'name': 'Promotion',
        'model_class': 'promotion.Promotion',
        'path': ['promotions']
    },
    {
        'name': 'Notification',
        'model_class': 'notification.Notification',
        'path': ['notifications']
    },
    {
        'name': 'Loyalty Program',
        'model_class': None,
        'path': ['benefits', 'coupons', 'pointgain', 'exchanges', 'quests', 'rankconfs']
    }
]
"""