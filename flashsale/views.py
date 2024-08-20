from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import *
from .serializers import *
from .utils.utils import *
from eco_sys.permissions import IsMerchant
from django.db.models import F


# Create your views here.
class FlashsaleUserView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']
    filterset_fields = ['name']
    serializer_class = FlashsaleSerializer
    model_class = Flashsale
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            data = ViewUtils.get_response(
                self,
                request,
                FlashsaleDetailSerializer,
                Flashsale.objects.get(pk=kwargs['pk'], shop__buyer__user=request.user)
            )
            return Response(data, status=data['status'])
        else:
            data = ViewUtils.paginated_get_response(
                self,
                request,
                FlashsaleSerializer,
                Flashsale.objects.filter(shop__buyer__user=request.user).distinct()
            )
            return Response(data, status=data['status'])
        
class FlashsaleShopView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']
    filterset_fields = ['name']
    serializer_class = FlashsaleSerializer
    model_class = Flashsale
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            data = ViewUtils.get_response(
                self,
                request,
                FlashsaleDetailSerializer,
                Flashsale.objects.get(pk=kwargs['pk'], shop__merchant=request.user)
            )
            return Response(data, status=data['status'])
        else:
            data = ViewUtils.paginated_get_response(
                self,
                request,
                FlashsaleSerializer,
                Flashsale.objects.filter(shop__merchant=request.user)
            )
            return Response(data, status=data['status'])
        
    def post(self, request, *args, **kwargs):
        items = request.data['items'] if 'items' in request.data else [request.data]
        shop = Shop.objects.filter(merchant=request.user).first()
        items = [{ 'shop': shop.id, **item } for item in items]
        serializer = FlashsaleSerializer(data=items, many=True)
        if not serializer.is_valid():
            data=ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Flashsale validation failed',data=serializer.errors)
            return Response(data, status=data['status'])
        serializer.save()
        data=ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='Flashsale created successfully',data=serializer.data)
        return Response(data, status=data['status'])
    
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Item id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Item not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance, data=item, partial=True)
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
            [item.save() for item in serializer_]
        # try:
        # except Exception as e:
        #     data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
        #     return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Items updated successfully.', data=f'Number of Items updated: {len(serializer_)}')
        return Response(data, status=data['status'])
    
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Item id must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = self.model_class.deleted.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Item not found or not deleted.')
                    return Response(data, data['status'])
                instance_.append(instance)
            try:
                [item.restore() for item in instance_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Items restored successfully.', data=f'Number of Items restored: {len(instance_)}')
            return Response(data, data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Item id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Item not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance)
                
                serializer_.append(serializer)
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Items deleted successfully.', data=f'Number of Items deleted: {len(serializer_)}')
            return Response(data, data['status'])

class FlashsaleLimitShopView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['type', 'unit']
    filterset_fields = ['type', 'unit']
    serializer_class = FlashsaleLimitSerializer
    model_class = FlashsaleLimit
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            data = ViewUtils.get_response(
                self,
                request,
                FlashsaleLimitDetailSerializer,
                FlashsaleLimit.objects.get(pk=kwargs['pk'])
            )
            return Response(data, status=data['status'])
        else:
            data = ViewUtils.paginated_get_response(
                self,
                request,
                FlashsaleLimitSerializer,
                FlashsaleLimit.objects.all()
            )
            return Response(data, status=data['status'])

class FlashsaleLimitManageView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['type', 'unit']
    filterset_fields = ['type', 'unit']
    serializer_class = FlashsaleLimitSerializer
    model_class = FlashsaleLimit
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            data = ViewUtils.get_response(
                self,
                request,
                FlashsaleLimitDetailSerializer,
                FlashsaleLimit.objects.get(pk=kwargs['pk'])
            )
            return Response(data, status=data['status'])
        else:
            data = ViewUtils.paginated_get_response(
                self,
                request,
                FlashsaleLimitSerializer,
                FlashsaleLimit.objects.all()
            )
            return Response(data, status=data['status'])
        
    def post(self, request, *args, **kwargs):
        items = request.data['items'] if 'items' in request.data else [request.data]
        serializer = FlashsaleLimitSerializer(data=items, many=True)
        if not serializer.is_valid():
            data=ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='FlashsaleLimit validation failed',data=serializer.errors)
            return Response(data, status=data['status'])
        serializer.save()
        data=ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='FlashsaleLimit created successfully',data=f'Items created: {len(serializer.data)}')
        return Response(data, status=data['status'])
    
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Item id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Item not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance, data=item, partial=True)
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
            [item.save() for item in serializer_]
        # try:
        # except Exception as e:
        #     data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
        #     return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Items updated successfully.', data=f'Number of Items updated: {len(serializer_)}')
        return Response(data, status=data['status'])
    
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Item id must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = self.model_class.deleted.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Item not found or not deleted.')
                    return Response(data, data['status'])
                instance_.append(instance)
            try:
                [item.restore() for item in instance_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Items restored successfully.', data=f'Number of Items restored: {len(instance_)}')
            return Response(data, data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Item id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Item not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance)
                
                serializer_.append(serializer)
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Items deleted successfully.', data=f'Number of Items deleted: {len(serializer_)}')
            return Response(data, data['status'])

class FlashsaleProductView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['product__name']
    filterset_fields = []
    serializer_class = FlashsaleProductSerializer
    model_class = FlashsaleProduct
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            data = ViewUtils.paginated_get_response(
                self,
                request,
                FlashsaleProductDetailSerializer,
                FlashsaleProduct.objects.get(pk=kwargs['pk'], flashsale__shop__merchant=request.user)
            )
            return Response(data, status=data['status'])
        else:
            data = ViewUtils.paginated_get_response(
                self,
                request,
                FlashsaleProductSerializer,
                FlashsaleProduct.objects.filter(flashsale__shop__merchant=request.user)
            )
            return Response(data, status=data['status'])
        
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Item id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Item not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance, data=item, partial=True)
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
            [item.save() for item in serializer_]
        # try:
        # except Exception as e:
        #     data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
        #     return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Items updated successfully.', data=f'Number of Items updated: {len(serializer_)}')
        return Response(data, status=data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Item id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Item not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance)
                
                serializer_.append(serializer)
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Items deleted successfully.', data=f'Number of Items deleted: {len(serializer_)}')
            return Response(data, data['status'])

class FlashsaleConditionView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['product__name']
    filterset_fields = []
    serializer_class = FlashsaleConditionSerializer
    model_class = FlashsaleCondition
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            data = ViewUtils.paginated_get_response(
                self,
                request,
                FlashsaleProductDetailSerializer,
                FlashsaleCondition.objects.get(pk=kwargs['pk'], flashsale__shop__merchant=request.user)
            )
            return Response(data, status=data['status'])
        else:
            data = ViewUtils.paginated_get_response(
                self,
                request,
                FlashsaleConditionSerializer,
                FlashsaleCondition.objects.filter(flashsale__shop__merchant=request.user)
            )
            return Response(data, status=data['status'])
        
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Item id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Item not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance, data=item, partial=True)
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
            [item.save() for item in serializer_]
        # try:
        # except Exception as e:
        #     data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
        #     return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Items updated successfully.', data=f'Number of Items updated: {len(serializer_)}')
        return Response(data, status=data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Item id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Item not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance)
                
                serializer_.append(serializer)
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Items deleted successfully.', data=f'Number of Items deleted: {len(serializer_)}')
            return Response(data, data['status'])

