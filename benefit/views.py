from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import *
from .serializers import *
from .utils.utils import *
from eco_sys.permissions import IsMerchant


# Create your views here.
class DefaultBenefitShopView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    model_class = DefaultBenefit
    serializer_class = DefaultBenefitSerializer
    
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['id', 'benefit_type', 'benefit_value']
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
        
class BenefitUserView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    model_class = UserBenefit
    serializer_class = UserBenefitSerializer
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['id', 'shop', 'rank','is_default']
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(user=request.user, id=kwargs['pk'])
            )
            return Response(respn, status=respn['status'])
        else:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(user=request.user),
            )
            return Response(respn, status=respn['status'])

class BenefitConfigShopView(mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    model_class = ConfigBenefit
    serializer_class = ConfigBenefitSerializer
    
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['id', 'default_benefit', 'rank_required', 'enabled', 'config_amount']
    ordering_fields = ['created_at', 'updated_at','config_amount']
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(id=kwargs['pk'], rank_required__shop__merchant=request.user)
            )
            return Response(respn, status=respn['status'])
        else:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(rank_required__shop__merchant=request.user),
            )
            return Response(respn, status=respn['status'])
    
    def post(self, request, *args, **kwargs):
        #* data : { [{ rank, shop, required_point, enabled, benefits }] }
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
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class.__name__} id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id'],rank_required__shop__merchant=request.user).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class.__name__} not found.')
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
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class.__name__} id must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = self.model_class.deleted.filter(id=item['id'],rank_required__shop__merchant=request.user).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class.__name__} not found or not deleted.')
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
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class.__name__} id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id'],rank_required__shop__merchant=request.user).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class.__name__} not found.')
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



class BenefitsShopView(mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    model_class = UserBenefit
    serializer_class = UserBenefitSerializer
    
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['id', 'user', 'benefit']
    ordering_fields = ['created_at', 'updated_at']
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(shop__merchant=request.user,id=kwargs['pk'])
            )
            return Response(respn, status=respn['status'])
        else:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(shop__merchant=request.user,),
            )
            return Response(respn, status=respn['status'])
    
    def post(self, request, *args, **kwargs):
        #* data : { [{ name, price, in_stock }] }
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
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class.__name__} id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(shop__merchant=request.user,id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class.__name__} not found.')
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
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class.__name__} id must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = self.model_class.deleted.filter(shop__merchant=request.user,id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class.__name__} not found or not deleted.')
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
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class.__name__} id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(shop__merchant=request.user,id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class.__name__} not found.')
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

class DefaultBenefitManageView(mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    model_class = DefaultBenefit
    serializer_class = DefaultBenefitSerializer
    
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['id', 'benefit_type', 'benefit_value']
    ordering_fields = ['created_at', 'updated_at']
    
    def get(self, request, *args, **kwargs):
        queryset = self.model_class.deleted.all() if request.data.get('getting_deleted') else self.model_class.objects.all()
        if 'pk' in kwargs:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                queryset.filter(id=kwargs['pk'])
            )
            return Response(respn, status=respn['status'])
        else:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                queryset.all(),
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
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class.__name__} id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class.__name__} not found.')
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
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class.__name__} id must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = self.model_class.deleted.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class.__name__} not found or not deleted.')
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
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message=f'{self.model_class.__name__} id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message=f'{self.model_class.__name__} not found.')
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