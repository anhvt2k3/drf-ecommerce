from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import *
from .utils.utils import *
from eco_sys.permissions import IsMerchant
from .filters import *


# Create your views here.
class NotificationUserView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    model_class = Notification
    queryset = Notification.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filter_class = ['type','title','message','read_status','priority','additional_data']
    search_fields = ['title','message','shop__name']
    ordering_fields = ['created_at','updated_at']
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            data = ViewUtils.get_response(
                self,
                request,
                NotificationDetailSerializer,
                self.model_class.objects.get(pk=kwargs['pk'], shop__buyer__user=request.user)
            )
            return Response(data, status=data['status'])
        else:
            data = ViewUtils.paginated_get_response(
                self,
                request,
                self.serializer_class,
                self.model_class.objects.filter(shop__buyer__user=request.user).distinct()
            )
            return Response(data, status=data['status'])