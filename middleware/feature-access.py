from django.http import HttpResponseForbidden

from subscription.models import TierFeature

class FeatureAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Example of getting the user's tier and the feature they're accessing
        tier = request.user.subscription.tier
        feature = self.get_feature_from_request(request)
        feature_limits = TierFeature.objects.filter(tier=tier, feature=feature).values('limitation').first()
        progression = request.user.subscription.progress_set.filter(feature=feature).first().progression
        
        for f, v in feature_limits.items():
            if progression.get(f, 0) >= v:
                return HttpResponseForbidden("Feature limit exceeded")
            
        # Proceed with the request
        return self.get_response(request)

    def get_feature_from_request(self, request):
        # Extract the feature based on the request path, e.g., from the URL
        path = request.path
        if 'my' not in path:
            return None
        
        if 'flashsales' in path:
            return 'Flashsale'
        elif 'promotions' in path:
            return 'Promotion'
        elif 'notifications' in path:
            return 'Notification'
        elif ['benefits', 'coupons', 'pointgain', 'exchanges', 'quests', 'rankconfs'] in path:
            return 'Loyalty Program'
        
        return None