from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from rank.serializers import RankConfigSerializer
from shop.filters import PointGainFilter

from .models import *
from .serializers import *
from .utils.utils import *
from eco_sys.permissions import IsMerchant


# Create your views here.
class ShopMerchantView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    model_class = Shop
    serializer_class = ShopSerializer
    
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['id', 'name']
    ordering_fields = ['id', 'name', 'price', 'in_stock']
    
    def get(self, request, *args, **kwargs):
        respn = ViewUtils.paginated_get_response(
            self,
            request,
            self.serializer_class,
            self.model_class.objects.filter(merchant=request.user.id),
        )
        return Response(respn, status=respn['status'])
        
    def post(self, request, *args, **kwargs):
        item = request.data
        item['merchant'] = request.user.id
        
        serializer_ = []
        shop_seri = ShopSerializer(data=item)
        if not shop_seri.is_valid():
            data = ViewUtils.gen_response(data=shop_seri.errors)
            return Response(data, data['status'])
        serializer_.append(shop_seri)
        
        try:
            [seri.save() for seri in serializer_]
        except Exception as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
            return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message=f'{self.model_class.__name__} created successfully.', data=f'Items created: {len(serializer_)}')
        return Response(data=data, status=data['status'])

class BuyerShopView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    model_class = Buyer
    serializer_class = BuyerSerializer
    
    def get(self, request, *args, **kwargs):
        respn = ViewUtils.paginated_get_response(
            self,
            request,
            self.serializer_class,
            self.model_class.objects.filter(shop__merchant=request.user.id),
        )
        return Response(respn, status=respn['status'])
        
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class} id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id'], shop__merchant=request.user.id).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class} not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance, data=item, partial=True)
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
                
            try:
                [item.save() for item in serializer_]
            except serializers.ValidationError as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message=f'{self.model_class.__name__} updated successfully.', data=f'Number of {self.model_class.__name__} updated: {len(serializer_)}')
            return Response(data, status=data['status'])
    
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class} id must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = self.model_class.deleted.filter(id=item['id'], shop__merchant=request.user.id).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class} not found or not deleted.')
                    return Response(data, data['status'])
                instance_.append(instance)
            try:
                [item.restore() for item in instance_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message=f'{self.model_class.__name__} restored successfully.', data=f'Number of {self.model_class.__name__} restored: {len(instance_)}')
            return Response(data, data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class} id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id'], shop__merchant=request.user.id).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class} not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance)
                serializer_.append(serializer)
                
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message=f'{self.model_class.__name__} deleted successfully.', data=f'Number of {self.model_class.__name__} deleted: {len(serializer_)}')
            return Response(data, data['status'])

class BuyerUserView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    model_class = Buyer
    serializer_class = BuyerSerializer
    
    def get(self, request, *args, **kwargs):
        respn = ViewUtils.paginated_get_response(
            self,
            request,
            self.serializer_class,
            self.model_class.objects.filter(user=request.user.id),
        )
        return Response(respn, status=respn['status'])
            
    def post(self, request, *args, **kwargs):
        item = request.data
        item['user'] = request.user.id
        
        serializer_ = []
        buyer_seri = self.serializer_class(data=item)
        if not buyer_seri.is_valid():
            data = ViewUtils.gen_response(data=buyer_seri.errors)
            return Response(data, data['status'])
        try:
            serializer_.append(buyer_seri)
            buyer_seri.save()
        except Exception as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
            return Response(data, data['status'])
        
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message=f'{self.model_class.__name__} created successfully.', data=f'Items created: {len(serializer_)}')
        return Response(data=data, status=data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class} id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id'], user=request.user.id).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class} not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance)
                serializer_.append(serializer)
                
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message=f'{self.model_class.__name__} deleted successfully.', data=f'Number of {self.model_class.__name__} deleted: {len(serializer_)}')
            return Response(data, data['status'])

class PointGainBuyerView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    model_class = PointGain
    serializer_class = PointGainSerializer
    
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PointGainFilter
    search_fields = ['id','quest','gain_point']
    ordering_fields = ['created_at', 'updated_at']
    
    def get(self, request, *args, **kwargs):
        respn = ViewUtils.paginated_get_response(
            self,
            request,
            self.serializer_class,
            self.model_class.objects.filter(buyer__user=request.user),
        )
        return Response(respn, status=respn['status'])
            
class PointGainShopView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    model_class = PointGain
    serializer_class = PointGainSerializer
    
    def get(self, request, *args, **kwargs):
        respn = ViewUtils.paginated_get_response(
            self,
            request,
            self.serializer_class,
            self.model_class.objects.filter(buyer__shop__merchant=request.user),
        )
        return Response(respn, status=respn['status'])

class ShopManageView(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        generics.GenericAPIView):
    model_class = Shop
    serializer_class = ShopSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['id', 'name']
    ordering_fields = ['created_at', 'updated_at']
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(id=kwargs['pk'])
            )
            return Response(respn, status=respn['status'])
        else:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.all(),
            )
            return Response(respn, status=respn['status'])
    
    def post(self, request, *args, **kwargs):
        items = request.data.get('items') if 'items' in request.data else [request.data]
        serializer_ = []
        for item in items:
            serializer = self.serializer_class(data=item)
            if not serializer.is_valid():
                data = ViewUtils.gen_response(data=serializer.errors)
                return Response(data, data['status'])
            serializer_.append(serializer)
        try:
            [item.save() for item in serializer_]
        except Exception as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
            return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message=f'{self.model_class.__name__} created successfully.', data=f'{self.model_class.__name__} created: {len(serializer_)}')
        return Response(data=data, status=data['status'])
        
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class} id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class} not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance, data=item, partial=True)
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
                
            try:
                [item.save() for item in serializer_]
            except serializers.ValidationError as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message=f'{self.model_class.__name__} updated successfully.', data=f'Number of {self.model_class.__name__} updated: {len(serializer_)}')
            return Response(data, status=data['status'])
    
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class} id must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = self.model_class.deleted.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class} not found or not deleted.')
                    return Response(data, data['status'])
                instance_.append(instance)
            try:
                [item.restore() for item in instance_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message=f'{self.model_class.__name__} restored successfully.', data=f'Number of {self.model_class.__name__} restored: {len(instance_)}')
            return Response(data, data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class} id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class} not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance)
                serializer_.append(serializer)
                
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message=f'{self.model_class.__name__} deleted successfully.', data=f'Number of {self.model_class.__name__} deleted: {len(serializer_)}')
            return Response(data, data['status'])