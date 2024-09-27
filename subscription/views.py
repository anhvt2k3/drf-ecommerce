from rest_framework import generics, mixins
from rest_framework.response import Response
from eco_sys.permissions import IsAdminUser, IsAuthenticated, IsMerchant
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import *
from .serializers import *
from .utils.utils import *


# Create your views here.
class PaymentUserView(generics.GenericAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        user = request.user
        data = ViewUtils.paginated_get_response(
                    self,
                    request,
                    self.serializer_class,
                    Payment.objects.filter(user=user)                                                
                )
        return Response(data, data['status'])
    
    def post(self, request):
        serializer = self.serializer_class(data={'user': request.user.id, **request.data})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message="Payment credentials have been stored successfully.", data=serializer.data)
        return Response(data, data['status'])