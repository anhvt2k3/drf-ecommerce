from django.shortcuts import redirect
from eco_sys.permissions import IsMerchant
from order.filters import OrderUserFilterSet
from payment.models import Payment
from shop.models import Shop
from .models import Order
from .serializers import *
from eco_sys.utils import *
from eco_sys.secrets import STRIPE_SECRET_KEY, NGROK_DOMAIN, STRIPE_WEBHOOK_SECRET
from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

# Create your views here.
class OrderShopView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    model_class = Order
    serializer_class = OrderSerializer
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'created_at', 'updated_at']
    search_fields = ['id', 'created_at', 'updated_at']
    ordering_fields = ['id', 'created_at', 'updated_at']

    def get(self, request, *args, **kwargs):
        shop = Shop.objects.filter(merchant=request.user).first()
        orders = Order.objects.filter(orderitem__product__shop=shop).exclude(status='pending').distinct()
        data = ViewUtils.paginated_get_response(
            self,
            request,
            OrderSerializer,
            orders
        )
        return Response(data, data['status'])
    
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
            shop = Shop.objects.filter(merchant=request.user).first()
            orders = Order.objects.filter(orderitem__product__shop=shop).exclude(status='pending').distinct()
            for item in items:
                instance = orders.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Item not found.')
                    return Response(data, data['status'])
                serializer = OrderSerializer(instance, data=item, partial=True)
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
            try:
                [item.save() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Items updated successfully.', data=f'Number of Items updated: {len(serializer_)}')
            return Response(data, status=data['status'])

class OrderItemShopView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    model_class = OrderItem
    serializer_class = OrderItemSerializer
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'order', 'product', 'quantity', 'created_at', 'updated_at']
    ordering_fields = ['id', 'order', 'product', 'quantity', 'created_at', 'updated_at']
    search_fields = ['id', 'order', 'product']

    def get(self, request, *args, **kwargs):
        shop = Shop.objects.filter(merchant=request.user).first()
        orders = Order.objects.filter(orderitem__product__shop=shop).exclude(status='pending').distinct()
        data = ViewUtils.paginated_get_response(
            self,
            request,
            OrderItemSerializer,
            OrderItem.objects.filter(order__in=orders)
        )
        return Response(data, data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Orderitem id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            shop = Shop.objects.filter(merchant=request.user).first()
            orders = Order.objects.filter(orderitem__product__shop=shop).exclude(status='pending').distinct()
            orderitems = OrderItem.objects.filter(order__in=orders)
            for item in items:
                instance = orderitems.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Orderitem not found.')
                    return Response(data, data['status'])
                serializer = OrderItemSerializer(instance)
                serializer_.append(serializer)
                
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Items deleted successfully.', data=f'Number of Items deleted: {len(serializer_)}')
            return Response(data, data['status'])
    
    
    
    
class CheckoutView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data={'user':request.user.id, **request.data})
        if serializer.is_valid():
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='Checkout created successfully.', data=serializer.data)
            return Response(data, status=data['status'])
        data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=serializer.errors)
        return Response(data, status=data['status'])
        
    
class OrderUserView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    model_class = Order
    serializer_class = OrderUserSerializer
    
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OrderUserFilterSet
    search_fields = ['id']
    ordering_fields = ['id', 'created_at', 'updated_at']
    
    def get(self, request, *args, **kwargs):
        if 'getting_deleted' in request.data and request.data['getting_deleted']:
            data = ViewUtils.paginated_get_response(
                self,
                request, 
                OrderUserSerializer,
                Order.deleted.filter(user=request.user)
            )
            return Response(data, data['status'])
        elif 'pk' not in kwargs:
            data = ViewUtils.paginated_get_response(
                self,
                request, 
                OrderUserSerializer,
                Order.objects.filter(user=request.user)
            )
            return Response(data, data['status'])
        elif 'getting_items' in request.data and request.data['getting_items']:
            order = Order.objects.filter(id=kwargs['pk'], user=request.user)
            data = ViewUtils.paginated_get_response(
                self,
                request,
                OrderItemSerializer,
                OrderItem.objects.filter(order__in=order)
            )
            return Response(data, data['status'])
        else:
            data = ViewUtils.paginated_get_response(
                self,
                request,
                OrderUserSerializer,
                Order.objects.filter(id=kwargs['pk'], user=request.user)
            )
            return Response(data, data['status'])
    
    def post(self, request, *args, **kwargs):
        items = request.data.get('items') if 'items' in request.data else [request.data]
        [item.update({'user':request.user.id}) for item in items]
        serializer = OrderUserSerializer(data=items, many=True)
        # try:
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        data=ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='Items created successfully.', data=serializer.data)
        return Response(data, status=data['status'])
        # except serializers.ValidationError as e:
        #     data = ViewUtils.gen_response(message='An error occurred while validating.', data=e.detail)
        #     return Response(data, data['status'])
        # except Exception as e:
        #     data = ViewUtils.gen_response(message='An error occurred while creating.', data=str(e))
        #     return Response(data, data['status'])

    #@ restore 1/many orders with all its orderitems
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Order id must be provided.')
            return Response(data, data['status'])
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            restore_set = []
            for item in items:
                order = Order.deleted.filter(id=item['id'], user=request.user).first()
                if not order:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Order not found.')
                    return Response(data, data['status'])
                order_seri = OrderUserSerializer(order)
                restore_set.append(order_seri)
            try:
                [item.restore() for item in restore_set]
                pass
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Orders restored successfully.', data=f'Number of orders and orderitems restored: {len(restore_set)}')
            return Response(data, data['status'])
                
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Order id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = Order.objects.filter(id=item['id'],user=request.user).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Order not found.')
                    return Response(data, data['status'])
                serializer = OrderUserSerializer(instance)
                serializer_.append(serializer)
                
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Orders deleted successfully.', data=f'Number of Orders deleted: {len(serializer_)}')
            return Response(data, data['status'])

class OrderItemUserView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    model_class = OrderItem
    serializer_class = OrderItemSerializer
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'order', 'product', 'quantity', 'created_at', 'updated_at']
    ordering_fields = ['id', 'order', 'product', 'quantity', 'created_at', 'updated_at']
    search_fields = ['product__shop__name', 'product__name']
    
    def get(self, request, *args, **kwargs):
        orders = Order.objects.filter(user=request.user)
        if request.data.get('getting_deleted'):
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.deleted.filter(order__in=Order.deleted.filter(user=request.user))
            )
            return Response(respn, status=respn['status'])
        elif 'pk' in kwargs:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(id=kwargs['pk'], order__in=orders)
            )
            return Response(respn, status=respn['status'])
        else:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(order__in=orders),
            )
            return Response(respn, status=respn['status'])
    
    #@ add 1/many orderitems to an order
    def post(self, request, *args, **kwargs):
        #* data : { [{ product,quantity }] }
        if 'pk' not in kwargs:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Order id not provided.')
            return Response(data, data['status'])
        
        else:
            order = Order.objects.filter(id=kwargs['pk'], user=request.user).first()
            shop = order.orderitem_set.first().product.shop
            if not order:
                data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Order not found.')
                return Response(data, data['status'])
            items = request.data.get('items') if 'items' in request.data else [request.data]
            serializer_ = []
            for item in items:
                if Product.objects.filter(id=item['product']).first().shop != shop:
                    data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Product not belong to the shop of this order.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(data={ 'order':order.id,**item })
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
            try:
                [item.save() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='OrderItem Items created successfully.', data=f'Number of items created: {len(serializer_)}')
            return Response(data=data, status=data['status'])
        
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='OrderItem id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id'],order__in=Order.objects.filter(user=request.user)).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='OrderItem not found in user OrderItem set.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance, data=item, partial=True)
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
            try:
                [item.save() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='OrderItems updated successfully.', data=f'Number of OrderItems updated: {len(serializer_)}')
            return Response(data, status=data['status'])
    
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='OrderItem id must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = self.model_class.deleted.filter(id=item['id'],order__in=Order.objects.filter(user=request.user)).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='OrderItem is not deleted or not belong to user.')
                    return Response(data, data['status'])
                instance_order = instance.order
                if Order.deleted.filter(id=instance_order.id,user=request.user).first():
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='The Order of this order item is deleted. Restore the Order first!.', data=OrderItemSerializer(instance).data)
                    return Response(data, data['status'])
                instance_.append(instance)
            try:
                [item.restore() for item in instance_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='OrderItems restored successfully.', data=f'Number of OrderItems restored: {len(instance_)}')
            return Response(data, data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='OrderItem id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id'], order__in=Order.objects.filter(user=request.user)).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='OrderItem not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance)
                serializer_.append(serializer)
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='OrderItems deleted successfully.', data=f'Number of OrderItems deleted: {len(serializer_)}')
            return Response(data, data['status'])



class PaymentView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        paid_orders = Order.objects.filter(user=request.user, status='paid')
        data = ViewUtils.paginated_get_response(
            self,
            request,
            OrderPaidSerializer,
            paid_orders
        )
        return Response(data, data['status'])
    
    def post(self, request, *args, **kwargs):
        pi = OrderPaidSerializer(data=request.data)
        if not pi.is_valid():
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Invalid data.', data=pi.errors)
            return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Payment successful.', data=pi.data)
        return Response(data, status=data['status'])

# class PaymentSuccessView(generics.GenericAPIView):
#     def get(self, request, *args, **kwargs):
#         data=ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Payment successful.', data='Payment successful.')
#         return Response(data, status=data['status'])

# class PaymentCancelView(generics.GenericAPIView):
#     def get(self, request, *args, **kwargs):
#         data=ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Payment failed.', data='Payment failed.')
#         return Response(data, status=data['status'])

class OrderItemManageView(
    mixins.ListModelMixin, mixins.UpdateModelMixin,
    mixins.DestroyModelMixin, generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    model_class = OrderItem
    serializer_class = OrderItemSerializer
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'order', 'product', 'quantity', 'created_at', 'updated_at']
    search_fields = ['id', 'order', 'product']
    ordering_fields = ['id', 'order', 'product', 'quantity', 'created_at', 'updated_at']
    
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
        #* data : { [{ order,product,quantity... }] }
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
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='Order Items created successfully.', data=f'Order Items created: {len(serializer_)}')
        return Response(data=data, status=data['status'])
        
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Order Item id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Order Item not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance, data=item, partial=True)
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
        try:
            [item.save() for item in serializer_]
        except Exception as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
            return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Order Items updated successfully.', data=f'Number of Order Items updated: {len(serializer_)}')
        return Response(data, status=data['status'])
    
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Order Item id must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = self.model_class.deleted.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Order Item not found or not deleted.')
                    return Response(data, data['status'])
                instance_.append(instance)
            try:
                [item.restore() for item in instance_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Order Items restored successfully.', data=f'Number of Order Items restored: {len(instance_)}')
            return Response(data, data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Order Item id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Order Item not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance)
                
                serializer_.append(serializer)
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Order Items deleted successfully.', data=f'Number of Order Items deleted: {len(serializer_)}')
            return Response(data, data['status'])
        
class OrderManageView(mixins.ListModelMixin, mixins.UpdateModelMixin,
    mixins.CreateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    model_class = Order
    serializer_class = OrderSerializer
    
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'user', 'created_at', 'updated_at']
    search_fields = ['id', 'user']
    ordering_fields = ['id', 'user', 'created_at', 'updated_at']
    
    
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
        #* data : { [{ user... }] }
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
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='Orders created successfully.', data=f'Orders created: {len(serializer_)}')
        return Response(data=data, status=data['status'])
        
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Order id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Order not found.')
                    return Response(data, data['status'])
                serializer = OrderSerializer(instance, data=item, partial=True)
                if serializer.is_valid():
                    serializer_.append(serializer)
                else:
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
            
            try:
                [item.save() for item in serializer_]
            except serializers.ValidationError as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Orders updated successfully.', data=f'Number of Orders updated: {len(serializer_)}')
            return Response(data, status=data['status'])
    
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Order id must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = self.model_class.deleted.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Order not found or not deleted.')
                    return Response(data, data['status'])
                instance_.append(instance)
            try:
                [item.restore() for item in instance_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Orders restored successfully.', data=f'Number of Orders restored: {len(instance_)}')
            return Response(data, data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Order id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Order not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance)
                
                serializer_.append(serializer)
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Orders deleted successfully.', data=f'Number of Orders deleted: {len(serializer_)}')
            return Response(data, data['status'])