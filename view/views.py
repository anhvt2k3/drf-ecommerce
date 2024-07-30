from product.serializers import ProductSerializer
from .models import View
from .serializers import *
from eco_sys.utils import *
from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


# Create your views here.
class ViewUserView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        view, isCreated = View.objects.get_or_create(user=user)
        if not isCreated: view.save()
        data = ViewUtils.paginated_get_response(
            self,
            request, 
            ViewSerializer,
            View.objects.filter(user=user)
        )
        return Response(data, data['status'])
    
class ViewItemUserView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    model_class = ViewItem
    serializer_class = ViewItemSerializer
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'view', 'product']
    ordering_fields = ['id', 'view', 'product']
    search_fields = ['id', 'product']
    
    def get(self, request, *args, **kwargs):
        user = request.user
        view, isCreated = View.objects.get_or_create(user=user)
        if not isCreated: view.save()
    #@ get all viewitems of a user
        if 'pk' not in kwargs:
            data = ViewUtils.paginated_get_response(
                self,
                request, 
                ViewItemSerializer, 
                ViewItem.objects.filter(view=view)
            )
            return Response(data, data['status'])
    #@ get 1 specific viewitem of a user
        elif 'pk' in kwargs:
            data = ViewUtils.paginated_get_response(
                self,
                request, 
                ViewItemSerializer, 
                ViewItem.objects.filter(view=view, id=kwargs.get('pk'))
            )
            return Response(data, data['status'])
    
    def post(self, request, *args, **kwargs):
        #* data : { [{ name, price, in_stock }] }
        view, iscreated = View.objects.get_or_create(user=request.user)
        if not iscreated: view.save()
        items = request.data.get('items') if 'items' in request.data else [request.data]
        serializer_ = []
        for item in items:
            serializer = ViewItemSerializer(data={ 'view':view.id, **item })
            if not serializer.is_valid():
                data = ViewUtils.gen_response(data=serializer.errors)
                return Response(data, data['status'])
            serializer_.append(serializer)
        try:
            [item.save() for item in serializer_]
        except Exception as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
            return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='View Items added successfully.', data=f'View Items created: {len(serializer_)}')
        return Response(data=data, status=data['status'])
    
class ViewItemManageView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    
    def get(self, request, *args, **kwargs):
    #@ get all viewitems of a view
        if 'pk' in kwargs:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                ViewItemSerializer,
                ViewItem.objects.filter(view=kwargs['pk'])
            )
            return Response(respn, status=respn['status_Code'])
    
    #@ get all viewitems of all views
        else:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                ViewItemSerializer,
                ViewItem.objects.all(),
            )
            return Response(respn, status=respn['status_Code'])
    
    def post(self, request, *args, **kwargs):
        #* data : { items : [{ view,product... }] } or { view,product... }
        items = request.data.get('items') if 'items' in request.data else [request.data]
        serializer_ = []
        for item in items:
            serializer = ViewItemSerializer(data=item)
            if not serializer.is_valid():
                data = ViewUtils.gen_response(data=serializer.errors)
                return Response(data, data['status'])
            serializer_.append(serializer)
        try:
            [item.save() for item in serializer_]
        except Exception as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
            return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='View Items added successfully.', data=f'View Items created: {len(serializer_)}')
        return Response(data=data, status=data['status'])
    
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='ViewItem id not provided.')
                return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id':kwargs.get('pk'), **request.data }]
            serializer_ = []
            for item in items:
                instance = ViewItem.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='ViewItem not found.')
                    return Response(data, data['status'])
                serializer = ViewItemSerializer(instance, data=item, partial=True)
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
        try:
            [item.save() for item in serializer_]
        except Exception as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
            return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='ViewItems updated successfully.', data=f'Number of ViewItems updated: {len(serializer_)}')
            return Response(data, status=data['status'])
    
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='ViewItem id not provided.')
                return Response(data, data['status'])
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id':kwargs.get('pk'), **request.data }]
            instance_ = []
            for item in items:
                instance = ViewItem.deleted.filter(id=item['id'])
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='ViewItem not found deleted.')
                    return Response(data, data['status'])
                instance = instance[0]
                instance_.append(instance)
            try:
                [item.restore() for item in instance_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='ViewItems updated successfully.', data=f'Number of ViewItems restored: {len(instance_)}')
            return Response(data, status=data['status'])
    
    #* data: { items: [{ id }] } or pk => id
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='View Item id not provided.')
            return Response(data, data['status'])
    
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id':kwargs.get('id'),**request.data }]
            serializer_ = []
            for item in items:
                instance = ViewItem.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='View Item not found.')
                    return Response(data, data['status'])
                serializer = ViewItemSerializer(instance)
                
                serializer_.append(serializer)
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='View Items deleted successfully.', data=f'Number of View Items deleted: {len(serializer_)}')
            return Response(data, data['status'])

class ViewManageView(mixins.ListModelMixin, mixins.UpdateModelMixin,
                mixins.CreateModelMixin ,mixins.DestroyModelMixin, generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    serializer_class = ViewSerializer
    model_class = View
    
    
    def get(self, request, *args, **kwargs):
    #@ get a view having id=pk
        if 'pk' in kwargs:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(id=kwargs['pk'])
            )
            return Response(respn, status=respn['status_Code'])
    
    #@ get all views
        else:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.all(),
            )
            return Response(respn, status=respn['status_Code'])
    
    def post(self, request, *args, **kwargs):
        items = request.data.get('items') if 'items' in request.data else [request.data]
        serializer_ = []
        for item in items:
            serializer = ViewSerializer(data=item)
            if not serializer.is_valid():
                data = ViewUtils.gen_response(data=serializer.errors)
                return Response(data, data['status'])
            serializer_.append(serializer)
        try:
            [item.save() for item in serializer_]
        except Exception as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
            return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='View Items added successfully.', data=f'View Items created: {len(serializer_)}')
        return Response(data=data, status=data['status'])
            
        
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='View id not provided.')
                return Response(data, data['status'])
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id':kwargs.get('pk'), **request.data }]
            serializer_ = []
            for item in items:
                instance = View.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='View not found.')
                    return Response(data, data['status'])
                serializer = ViewSerializer(instance, data=item, partial=True)
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
        try:
            [item.save() for item in serializer_]
        except Exception as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
            return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Views updated successfully.', data=f'Number of Views updated: {len(serializer_)}')
            return Response(data, status=data['status'])
    
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='View must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = View.deleted.filter(id=item['id'])
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='View not found or not deleted.')
                    return Response(data, data['status'])
                instance = instance[0]
                instance_.append(instance)
            try:
                [item.restore() for item in instance_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Views restored successfully.', data=f'Number of Views restored: {len(instance_)}')
            return Response(data, data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='View id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = View.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='View not found.')
                    return Response(data, data['status'])
                serializer = ViewSerializer(instance)
                
                serializer_.append(serializer)
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Views deleted successfully.', data=f'Number of Views deleted: {len(serializer_)}')
            return Response(data, data['status'])
