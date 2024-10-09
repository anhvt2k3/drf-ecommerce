from rest_framework import generics, mixins
from rest_framework.response import Response
from eco_sys.permissions import IsAdminUser, IsAuthenticated, IsMerchant
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import *
from .serializers import *
from .utils.utils import *


# Create your views here.
class ProgressionMerchantView(generics.GenericAPIView):
    serializer_class = ProgressSerializer
    permission_classes = [IsMerchant]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, *args, **kwargs):
        data = ViewUtils.paginated_get_response(
                    self,
                    request,
                    self.serializer_class,
                    Progress.objects.filter(user=request.user)                                                 
                )
        
        return Response(data, data['status'])
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message="Payment credentials have been stored successfully.", data=serializer.data)
        else:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message="Invalid data.", data=serializer.errors)
        return Response(data, data['status'])
    
class SubscriptionMerchantView(generics.GenericAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsMerchant]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, *args, **kwargs):
        data = ViewUtils.paginated_get_response(
                    self,
                    request,
                    self.serializer_class,
                    Subscription.objects.filter(user=request.user)                                                 
                )
        
        return Response(data, data['status'])
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message="Payment credentials have been stored successfully.", data=serializer.data)
        else:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message="Invalid data.", data=serializer.errors)
        return Response(data, data['status'])

class FeatureAdminView(generics.GenericAPIView):
    serializer_class = FeatureSerializer
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            data = ViewUtils.paginated_get_response(
                    self,
                    request,
                    FeatureDetailSerializer,
                    Feature.objects.get(id=kwargs['pk'])
                )
        else:
            data = ViewUtils.paginated_get_response(
                        self,
                        request,
                        self.serializer_class,
                        Feature.objects.filter()                                                
                    )
        return Response(data, data['status'])
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message="Payment credentials have been stored successfully.", data=serializer.data)
        else:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message="Invalid data.", data=serializer.errors)
        return Response(data, data['status'])
    
class TierAdminView(generics.GenericAPIView):
    serializer_class = TierSerializer
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            data = ViewUtils.paginated_get_response(
                    self,
                    request,
                    TierDetailSerializer,
                    Tier.objects.get(id=kwargs['pk'])
                )
        else:
            data = ViewUtils.paginated_get_response(
                        self,
                        request,
                        self.serializer_class,
                        Tier.objects.filter()                                                
                    )
        return Response(data, data['status'])
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message="Payment credentials have been stored successfully.", data=serializer.data)
        else:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message="Invalid data.", data=serializer.errors)
        return Response(data, data['status'])
    
class TierFeatureAdminView(generics.GenericAPIView):
    serializer_class = TierFeatureSerializer
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            data = ViewUtils.paginated_get_response(
                    self,
                    request,
                    TierFeatureDetailSerializer,
                    TierFeature.objects.get(id=kwargs['pk'])
                )
        else:
            data = ViewUtils.paginated_get_response(
                        self,
                        request,
                        self.serializer_class,
                        TierFeature.objects.filter()                                                
                    )
        return Response(data, data['status'])
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message="Payment credentials have been stored successfully.", data=serializer.data)
        else:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message="Invalid data.", data=serializer.errors)
        return Response(data, data['status'])
    
class PlanAdminView(generics.GenericAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            data = ViewUtils.paginated_get_response(
                    self,
                    request,
                    PlanDetailSerializer,
                    Plan.objects.get(id=kwargs['pk'])
                )
        else:
            data = ViewUtils.paginated_get_response(
                        self,
                        request,
                        self.serializer_class,
                        Plan.objects.filter()                                                
                    )
        return Response(data, data['status'])
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message="Payment credentials have been stored successfully.", data=serializer.data)
        else:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message="Invalid data.", data=serializer.errors)
        return Response(data, data['status'])
    