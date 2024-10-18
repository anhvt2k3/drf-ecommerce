# from django.utils.deprecation import MiddlewareMixin
from subscription.utils.utils import ViewUtils
from django.http import HttpResponse
from subscription.models import Feature, TierFeature

def decode_jwtNbind_user(request):
    import jwt
    from rest_framework_simplejwt.authentication import JWTAuthentication
    from rest_framework import exceptions
    
    # Get the token from the Authorization header
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if auth_header:
        try:
            # Extract the token from the header
            jwt_auth = JWTAuthentication()
            token = auth_header.split(' ')[1]  # Assuming the format is "Bearer <token>"
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token=validated_token)
            request.user = user
        except (IndexError, jwt.ExpiredSignatureError, jwt.InvalidTokenError, exceptions.AuthenticationFailed):
            request.user = None  # Or handle the authentication error appropriately
    else:
        request.user = None  # No token provided, set to None
    return request

class FeatureAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Example of getting the user's tier and the feature they're accessing
        #* Get the feature from the request
        if not (feature := self.get_feature_from_request(request)): 
            print ('No feature found ! Letting this go...')
            return self.get_response(request)
        
        #* Decode the JWT and bind the user to the request
        request = decode_jwtNbind_user(request)
        
        #* Check if the user has a shop and an active subscription
        if not (shop := request.user.shop_set.first()): return Response(status=403, data="User must have a Shop for this feature !")
        if not (cur_subscription := shop.subscription_set.filter(status='active').first()): return Response(status=403, data="No active subscription found for this shop !")
        tier = cur_subscription.tier
        
        #* Check if the user has the feature in their tier
        feature_limits = TierFeature.objects.filter(tier=tier, feature=feature).first().limitation
        progression = cur_subscription.progress_set.filter(feature=feature).first().progression
        
        #* Check if the user has reached the limit for the feature
        if (forbidResponse := self.limitNprogression_reconcile(
                                    feature_limits=feature_limits,
                                    progression=progression,
                                    shop=shop,
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
        features = Feature.objects.all()
        for feature in features:
            for path in feature.path:
                if path in fpath:
                    return feature
        return None
    
    def limitNprogression_reconcile(self, feature_limits, progression, shop, feature: Feature):
        # Check if the user has reached the limit for the feature
        from django.utils.timezone import datetime, timedelta
        from django.utils import timezone
        
        for f, v in feature_limits.items():
            print (f, v)
            if f == 'access' and v == 'none':
                return HttpResponse(status=403, content="Feature not available for this tier !")
            elif f == 'access' and v == 'unlimited':
                return None
            elif f == 'access' and v == 'limited':
                continue
            elif progression.get(f, 0) >= v:
                return HttpResponse(status=403, content=f"Feature limit reached for {feature.name} !")
            elif f == 'day-cap':
                now = timezone.now()
                #* Get the start of the current week (Monday)
                start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = start_of_day + timedelta(days=1)

                today_instances = feature.feature_instance.objects.filter(
                    shop=shop, 
                    created_at__range=(start_of_day, end_of_day)
                ).count()
                
                # print ('Today instances:', today_instances)
                if today_instances > v:
                    return HttpResponse(status=403, content=f"Feature limit reached for {feature.name} for today !")
            elif f == 'week-cap':
                now = timezone.now()
                #* Get the start of the current week (Monday)
                start_of_week = now - timedelta(days=now.weekday())  # Get the start of the current week (Monday)
                
                week_instances = feature.feature_instance.objects.filter(
                    shop=shop,
                    created_at__range=(start_of_week, now),
                ).count()
                
                # print ('Week instances:', week_instances)
                if week_instances > v:
                    return HttpResponse(status=403, content=f"Feature limit reached for {feature.name} for this week !")
        # return HttpResponse(status=403, content=f"Feature limit reached for {feature.name} for this week !")
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