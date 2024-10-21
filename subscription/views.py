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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    
    def get(self, request, *args, **kwargs):
        progress = Progress.objects.filter(subscription=Subscription.onDuties.filter(shop__merchant=request.user).first())
        [print (i.status, i.expire_date, timezone.now()) for i in Subscription.objects.filter()]
        print (Subscription.onDuties.filter(shop__merchant=request.user).first())
        print (progress)
        data = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                progress                                                 
            )
        
        return Response(data, data['status'])
    
class InvoiceMerchantView(generics.GenericAPIView):
    serializer_class = InvoiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    
    def get(self, request, *args, **kwargs):
        data = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                Invoice.objects.filter(subscription__shop__merchant=request.user)                                                 
            )
        
        return Response(data, data['status'])
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message="Objects in required are created successfully.", data=serializer.data)
            return Response(data, data['status'])
        else:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message="Invalid data.", data=serializer.errors)
            return Response(data, data['status'])
    
class SubscriptionMerchantView(generics.GenericAPIView):
    serializer_class = SubscriptionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    
    def get(self, request, *args, **kwargs):
        data = ViewUtils.paginated_get_response(
                    self,
                    request,
                    self.serializer_class,
                    Subscription.objects.filter(shop__merchant=request.user)                                                 
                )
        
        return Response(data, data['status'])
    
    def post(self, request):
        serializer = self.serializer_class(
                #! supposed that each user has 1 shop
                data={'shop':request.user.shop_set.first().id ,**request.data})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message="Objects in required are created successfully.", data=serializer.data)
            return Response(data, data['status'])
        else:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message="Invalid data.", data=serializer.errors)
            return Response(data, data['status'])
    
class PlanMerchantView(generics.GenericAPIView):
    serializer_class = PlanSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    
    def get(self, request, *args, **kwargs):
        data = ViewUtils.paginated_get_response(
                    self,
                    request,
                    self.serializer_class,
                    Plan.objects.filter()                                                 
                )
        
        return Response(data, data['status'])

class FeatureAdminView(generics.GenericAPIView):
    serializer_class = FeatureSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            data = ViewUtils.paginated_get_response(
                    self,
                    request,
                    FeatureDetailSerializer,
                    Feature.objects.filter(id=kwargs['pk'])
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
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message="Objects in required are created successfully.", data=serializer.data)
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
                    Tier.objects.filter(id=kwargs['pk'])
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
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message="Objects in required are created successfully.", data=serializer.data)
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
                    TierFeature.objects.filter(id=kwargs['pk'])
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
        items = request.data.get('items') if 'items' in request.data else [request.data]
        serializer = self.serializer_class(data=items, many=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message="Objects in required are created successfully.", data=serializer.data)
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
                    Plan.objects.filter(id=kwargs['pk'])
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
        items = request.data.get('items') if 'items' in request.data else [request.data]
        serializer = self.serializer_class(data=items, many=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message="Objects in required are created successfully.", data=serializer.data)
        else:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message="Invalid data.", data=serializer.errors)
        return Response(data, data['status'])
    