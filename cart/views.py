from .models import Cart
from .serializers import *
from rest_framework import generics, mixins, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

# Create your views here.
class CartUserView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        item, isCreated = Cart.objects.get_or_create(user=user)
        if not isCreated: item.save()
        data = ViewUtils.paginated_get_response(
            self,
            request, 
            CartSerializer,
            Cart.objects.filter(user=user)
        )
        return Response(data, data['status'])
    
    def patch(self, request, *args, **kwargs):
        cart = Cart.deleted.filter(user=request.user).first()
        seri_ = []
        if not cart:
            data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Cart is not created.')
            return Response(data, data['status'])
        cartitems = CartItem.deleted.filter(cart=cart)
        seri_.extend([CartItemSerializer(item) for item in cartitems])
        [item.restore() for item in cartitems]
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Cart items restored successfully.', data=f'Number of Items restored: {len(seri_)}')
        return Response(data, data['status'])
    
    def delete(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=request.user).first()
        seri_ = []
        if not cart:
            data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Cart is not created.')
            return Response(data, data['status'])
        cartitems = CartItem.objects.filter(cart=cart)
        seri_.extend([CartItemSerializer(item) for item in cartitems])
        [item.delete() for item in seri_]
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Cart emptied successfully.', data=f'Number of Items deleted: {len(seri_)}')
        return Response(data, data['status'])
    

class CartItemUserView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    model_class = CartItem
    serializer_class = CartItemSerializer
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'cart', 'product', 'quantity', 'price']
    ordering_fields = ['id', 'cart', 'product', 'quantity', 'price']
    search_fields = ['id', 'product']
    
    def get(self, request, *args, **kwargs):
        user = request.user
        table, isCreated = Cart.objects.get_or_create(user=user)
        if not isCreated: table.save()
        filter_args = { 'cart': table }
        filter_args.update({ 'id':kwargs.get('pk') } if 'pk' in kwargs else {})
        data = ViewUtils.paginated_get_response(
            self,
            request, 
            CartItemSerializer, 
            CartItem.objects.filter(**filter_args)
        )
        return Response(data, data['status'])
    
    ## Handle 2 add actions: add single or add bundle
    def post(self, request, *args, **kwargs):
    #*  data:   
    #*      { product, cart_quantity }
    #*  or  { items : [{ product, cart_quantity }] }
        cart, iscreated = Cart.objects.get_or_create(user=request.user)
        if not iscreated: cart.save()
        items = request.data.get('items') if 'items' in request.data else [request.data]
        serializer_ = []
        for item in items:
            serializer = CartItemSerializer(data={ 'cart':cart.id,**item })
            if not serializer.is_valid():
                data = ViewUtils.gen_response(data=serializer.errors)
                return Response(data, data['status'])
            serializer_.append(serializer)
        try:
            [item.save() for item in serializer_]
        except Exception as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
            return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='CartItems created successfully.', data=f'CartItems created: {len(serializer_)}')
        return Response(data=data, status=data['status'])

    def put(self, request, *args, **kwargs):
    #* data:
    #*     { id, product, quantity }
    #* or  { items : [{ id, product, quantity }] }
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Cart item id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id':kwargs.get('pk'), **request.data }]
            serializer_ = []
            for item in items:
                instance = CartItem.objects.filter(id=item['id'],cart=Cart.objects.filter(user=request.user).first()).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='CartItem not found.')
                    return Response(data, data['status'])
                serializer = CartItemSerializer(instance, data=item, partial=True)
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
        try:
            [item.save() for item in serializer_]
        except Exception as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
            return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='CartItems updated successfully.', data=f'Number of CartItems updated: {len(serializer_)}')
            return Response(data, status=data['status'])
    
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='CartItem id must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = CartItem.deleted.filter(id=item['id'],cart=Cart.objects.filter(user=request.user).first()).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='CartItem not found or not deleted.')
                    return Response(data, data['status'])
                instance_.append(instance)
            try:
                [item.restore() for item in instance_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='CartItems restored successfully.', data=f'Number of CartItems restored: {len(instance_)}')
            return Response(data, data['status'])
        
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='CartItem id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = CartItem.objects.filter(id=item['id'],cart=Cart.objects.filter(user=request.user).first()).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='CartItem not found.')
                    return Response(data, data['status'])
                serializer = CartItemSerializer(instance)
                
                serializer_.append(serializer)
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='CartItems deleted successfully.', data=f'Number of CartItems deleted: {len(serializer_)}')
            return Response(data, data['status'])

class CartManageView(mixins.ListModelMixin,
    generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    model_class = Cart
    serializer_class = CartSerializer
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'user']
    ordering_fields = ['id', 'user']
    search_fields = ['id', 'user']
    
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
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='Carts created successfully.', data=f'Carts created: {len(serializer_)}')
        return Response(data=data, status=data['status'])
        
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Cart id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Cart not found.')
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
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Carts updated successfully.', data=f'Number of Carts updated: {len(serializer_)}')
            return Response(data, status=data['status'])
    
    #@ utilized for restoring deleted Cart
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Cart id must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = self.model_class.deleted.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Cart not found or not deleted.')
                    return Response(data, data['status'])
                instance_.append(instance)
            try:
                [item.restore() for item in instance_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Carts restored successfully.', data=f'Number of Carts restored: {len(instance_)}')
            return Response(data, data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Cart id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Cart not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance)
                
                serializer_.append(serializer)
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Carts deleted successfully.', data=f'Number of Carts deleted: {len(serializer_)}')
            return Response(data, data['status'])
        
class CartItemManageView(mixins.ListModelMixin,
    generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    model_class = CartItem
    serializer_class = CartItemSerializer
    queryset = model_class.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'cart', 'product', 'quantity', 'price']
    ordering_fields = ['id', 'cart', 'product', 'quantity', 'price']
    search_fields = ['id', 'product']
    
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
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='Carts created successfully.', data=f'Items created: {len(serializer_)}')
        return Response(data=data, status=data['status'])
        
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Cart id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Cart not found.')
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
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Carts updated successfully.', data=f'Number of items updated: {len(serializer_)}')
            return Response(data, status=data['status'])
    
    #@ utilized for restoring deleted Cart
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Cart id must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = self.model_class.deleted.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Cart not found or not deleted.')
                    return Response(data, data['status'])
                instance_.append(instance)
            try:
                [item.restore() for item in instance_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Carts restored successfully.', data=f'Number of items restored: {len(instance_)}')
            return Response(data, data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Cart id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = self.model_class.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='Cart not found.')
                    return Response(data, data['status'])
                serializer = self.serializer_class(instance)
                
                serializer_.append(serializer)
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Carts deleted successfully.', data=f'Number of items deleted: {len(serializer_)}')
            return Response(data, data['status'])