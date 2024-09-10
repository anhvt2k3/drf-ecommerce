from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import *
from .utils.utils import *
from eco_sys.permissions import IsMerchant
from .filters import *


# Create your views here.
class RefundUserView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    model_class = Refund
    serializer_class = RefundSerializer
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            data = ViewUtils.paginated_get_response(
                self,
                request,
                RefundDetailSerializer,
                self.model_class.objects.filter(id=kwargs['pk'], order__user=request.user),
            )
            return Response(data, status=data['status'])
        else:
            data = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(order__user=request.user),
            )
            return Response(data, status=data['status'])
        
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data={'user': request.user.id, **request.data})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message="Refund request has been sent.", data=serializer.data)
        return Response(data, status=data['status'])
    
    def delete(self, request, *args, **kwargs):
        input = request.data
        refund = self.model_class.objects.filter(id=input['order'], order__user=request.user).first()
        if refund:
            refund.delete()
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message="Refund request has been deleted.")
        else:
            data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message="Refund request not found.")
            return Response(data, status=data['status'])

class RefundShopView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMerchant]
    model_class = Refund
    serializer_class = RefundSerializer
    
    def get(self, request, *args, **kwargs):
        orders = [order.id for order in Order.objects.all() if order.shop.merchant == request.user]
        refunds = Refund.objects.filter(order__id__in=orders)
        if 'pk' in kwargs:
            data = ViewUtils.paginated_get_response(
                self,
                request,
                RefundDetailSerializer,
                refunds.filter(id=kwargs['pk']),
            )
            return Response(data, status=data['status'])
        else:
            # print (f"User: {request.user}, type of user: {type(request.user)}")
            # [print (f'Order: {order.shop}') for order in Order.objects.filter(orderitem__product__shop__merchant=request.user).distinct()] 
            data = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                refunds,
            )
            return Response(data, status=data['status'])
        
    def put(self, request, *args, **kwargs):
        from .workers import perform_refund
        ## request.data = {'refund': <refund-id>}
        
        orders = [order.id for order in Order.objects.all() if order.shop.merchant == request.user]
        refunds = Refund.objects.filter(order__id__in=orders)
        input = request.data
        refund = refunds.filter(id=input['refund']).first()
        # if refund and refund.confirmation == False:
        if refund:
            refund.confirmation = True
            isOk, error = perform_refund(refund.order)
            if not isOk:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message="Refund request has been failed.", data=str(error))
                return Response(data, status=data['status'])
            refund.save()
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message="Refund request has been approved.")
            return Response(data, status=data['status'])
        ## offed for debugging
        # elif refund and refund.confirmation == True:
        #     data = ViewUtils.gen_response(success=True, status=HTTP_400_BAD_REQUEST, message="Refund request has been done.")
        #     return Response(data, status=data['status'])
        else:
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message="Refund request not found.")
            return Response(data, status=data['status'])