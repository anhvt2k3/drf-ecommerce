from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import *
from .utils.utils import *
from eco_sys.permissions import IsMerchant
from .filters import *


# Create your views here.
class PointExchangeUserView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    model_class = PointExchange
    serializer_class = PointExchangeSerializer
    
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['buyer', 'coupon', 'remain_usage']
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(buyer__in=request.user.buyer_set.all(),id=kwargs['pk'])
            )
            return Response(respn, status=respn['status'])
        else:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(buyer__in=request.user.buyer_set.all()),
            )
            return Response(respn, status=respn['status'])
    
    def post(self, request, *args, **kwargs):
        items = request.data.get('items') if 'items' in request.data else [request.data]
        ## create Buyer if User's never interacted with the Coupon.shop
        for item in items:
            shop = Coupon.objects.filter(id=item['coupon']).first().shop
            item['buyer'] = Buyer.objects.get_or_create(user=request.user.id, shop=shop.id)[0].id
        serializers = self.serializer_class(data=items, many=True)
        if not serializers.is_valid():
            data = ViewUtils.gen_response(message='An error occurred while validating items.', data=serializers.errors)
            return Response(data, data['status'])
        try:
            serializers.save()
        except Exception as e:
            data = ViewUtils.gen_response(message='An error occurred while creating items.', data=str(e))
            return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='Items created successfully.', data=f'Items created: {len(serializers.data)}')
        return Response(data=data, status=data['status'])
        
        
class PointExchangeShopView(generics.GenericAPIView):
    model_class = PointExchange
    serializer_class = PointExchangeSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
        
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['buyer', 'coupon', 'remain_usage']
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(buyer__shop__merchant=request.user,id=kwargs['pk'])
            )
            return Response(respn, status=respn['status'])
        else:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(buyer__shop__merchant=request.user)
            )
            return Response(respn, status=respn['status'])
    
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Product id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(buyer__shop__merchant=request.user,id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Product not found.')
                    return Response(data, data['status'])
                serializer = ProductSerializer(instance, data=item, partial=True)
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
                
            try:
                [item.save() for item in serializer_]
            except serializers.ValidationError as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Products updated successfully.', data=f'Number of products updated: {len(serializer_)}')
            return Response(data, status=data['status'])
    
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Product id must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = self.model_class.deleted.filter(buyer__shop__merchant=request.user,id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Product not found or not deleted.')
                    return Response(data, data['status'])
                instance_.append(instance)
            try:
                [item.restore() for item in instance_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Products restored successfully.', data=f'Number of products restored: {len(instance_)}')
            return Response(data, data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Product id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(buyer__shop__merchant=request.user,id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Product not found.')
                    return Response(data, data['status'])
                serializer = ProductSerializer(instance)
                serializer_.append(serializer)
                
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Products deleted successfully.', data=f'Number of Products deleted: {len(serializer_)}')
            return Response(data, data['status'])
    
    
    
    
    
    
    
# class ProductManageView(mixins.ListModelMixin,
#     mixins.CreateModelMixin,
#                      mixins.UpdateModelMixin,
#                      mixins.DestroyModelMixin,
#                      generics.GenericAPIView):
#     queryset = Product.objects.all()
#     model_class = Product
#     serializer_class = ProductSerializer
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAdminUser]
    
#     queryset = model_class.objects.all()
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
#     filterset_class = ProductAdminFilter
#     search_fields = ['id', 'name']
#     ordering_fields = ['id', 'name', 'price', 'in_stock', 'created_at', 'updated_at']
    
#     def get(self, request, *args, **kwargs):
#         if 'pk' in kwargs:
#             respn = ViewUtils.paginated_get_response(
#                 self,
#                 request,
#                 ProductSerializer,
#                 Product.objects.filter(id=kwargs['pk'])
#             )
#             return Response(respn, status=respn['status'])
#         else:
#             respn = ViewUtils.paginated_get_response(
#                 self,
#                 request,
#                 ProductSerializer,
#                 Product.objects.all(),
#             )
#             return Response(respn, status=respn['status'])
    
#     def post(self, request, *args, **kwargs):
#         #* data : { [{ name, price, in_stock }] }
#         items = request.data.get('items') if 'items' in request.data else [request.data]
#         serializer_ = []
#         for item in items:
#             serializer = ProductSerializer(data=item)
#             if not serializer.is_valid():
#                 data = ViewUtils.gen_response(data=serializer.errors)
#                 return Response(data, data['status'])
#             serializer_.append(serializer)
#         try:
#             [item.save() for item in serializer_]
#         except Exception as e:
#             data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
#             return Response(data, data['status'])
#         data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='Products created successfully.', data=f'Products created: {len(serializer_)}')
#         return Response(data=data, status=data['status'])
        
#     def put(self, request, *args, **kwargs):
#         if 'pk' in kwargs and 'items' in request.data:
#             data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
#             return Response(data, data['status'])
#         elif 'pk' not in kwargs and 'items' not in request.data:
#             data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Product id not provided.')
#             return Response(data, data['status'])
        
#         else:
#             items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
#             serializer_ = []
#             for item in items:
#                 instance = Product.objects.filter(id=item['id']).first()
#                 if not instance:
#                     data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Product not found.')
#                     return Response(data, data['status'])
#                 serializer = ProductSerializer(instance, data=item, partial=True)
#                 if not serializer.is_valid():
#                     data = ViewUtils.gen_response(data=serializer.errors)
#                     return Response(data, data['status'])
#                 serializer_.append(serializer)
                
#             try:
#                 [item.save() for item in serializer_]
#             except serializers.ValidationError as e:
#                 data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
#                 return Response(data, data['status'])
#             data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Products updated successfully.', data=f'Number of products updated: {len(serializer_)}')
#             return Response(data, status=data['status'])
    
#     #@ utilized for restoring deleted product
#     def patch(self, request, *args, **kwargs):
#         if 'pk' in kwargs and 'items' in request.data:
#             data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
#             return Response(data, data['status'])
#         elif 'pk' not in kwargs and 'items' not in request.data:
#             data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Product id must be provided.')
#             return Response(data, data['status'])
        
#         else:
#             items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
#             instance_ = []
#             for item in items:
#                 instance = Product.deleted.filter(id=item['id'])
#                 if not instance:
#                     data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Product not found or not deleted.')
#                     return Response(data, data['status'])
#                 instance = instance[0]
#                 instance_.append(instance)
#             try:
#                 [item.restore() for item in instance_]
#             except Exception as e:
#                 data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
#                 return Response(data, data['status'])
#             data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Products restored successfully.', data=f'Number of products restored: {len(instance_)}')
#             return Response(data, data['status'])
    
#     def delete(self, request, *args, **kwargs):
#         if 'pk' in kwargs and 'items' in request.data:
#             data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
#             return Response(data, data['status'])
#         elif 'pk' not in kwargs and 'items' not in request.data:
#             data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Product id not provided.')
#             return Response(data, data['status'])
        
#         else:
#             items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
#             serializer_ = []
#             for item in items:
#                 instance = Product.objects.filter(id=item['id']).first()
#                 if not instance:
#                     data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Product not found.')
#                     return Response(data, data['status'])
#                 serializer = ProductSerializer(instance)
                
#                 serializer_.append(serializer)
#             try:
#                 [item.delete() for item in serializer_]
#             except Exception as e:
#                 data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
#                 return Response(data, data['status'])
#             data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Products deleted successfully.', data=f'Number of Products deleted: {len(serializer_)}')
#             return Response(data, data['status'])