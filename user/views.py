
from eco_sys import settings
from .serializers import *
from .models import User
from eco_sys.utils import *
import urllib.parse
from django.shortcuts import redirect
import requests

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt import serializers, authentication

# Create your views here.
class UserRegisterView(generics.GenericAPIView):
    serializer_class = UserSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['password'] = make_password(serializer.validated_data['password'])
            serializer.save()
            data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='User created successfully!', data=serializer.data)
            return Response(data, data['status'])
        else:
            data = ViewUtils.gen_response(data=serializer.errors)
            return Response(data, data['status'])


class UserLoggedView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get(self, request, *args, **kwargs):
        data = ViewUtils.paginated_get_response(
            self,
            request,
            UserSerializer,
            User.objects.filter(id=request.user.id)
        )
        return Response(data, data['status'])

class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializers.authenticate(
                request,
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            if user:
                refresh = serializers.TokenObtainPairSerializer.get_token(user)
                data = {
                    'refresh_token': str(refresh),
                    'access_token': str(refresh.access_token)
                }
                return Response(data, status.HTTP_200_OK)

            return Response({
                'error_message': 'Mật khẩu hoặc tên người dùng bị sai!',
                'error_code': 400
            }, status.HTTP_400_BAD_REQUEST)

        return Response({
            'error_messages': serializer.errors,
            'error_code': 400
        }, status.HTTP_400_BAD_REQUEST)
        
class GoogleAuthView(generics.GenericAPIView):
    # serializer_class = UserSerializer
    def get(self, request):
        client_id = settings.GOOGLE_CLIENT_ID
        redirect_uri = 'http://localhost:8000/callback/google/'
        scope = 'openid email profile'
        state = 'authenticating'
        
        authorization_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'state': state,
        }
        url = f"{authorization_url}?{urllib.parse.urlencode(params)}"
        return redirect(url)

class GoogleCallbackView(generics.GenericAPIView):
    serializer_class = UserSerializer
    def get(self, request):
        code = request.GET.get('code')
        if not code:
            return redirect('me')  # Handle the error case
        # print (f'code {code}')
        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_CLIENT_SECRET
        
        #! Use the code to get the access token
        redirect_uri = 'http://localhost:8000/callback/google/'
        token_url = 'https://oauth2.googleapis.com/token'
        data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }
        r = requests.post(token_url, data=data)
        token_response = r.json()
        access_token = token_response.get('access_token')
        
        if not access_token:
            return redirect('me')  # Handle the error case
        
        #! Use the access token to get user info
        user_info_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()
        
        print (f'user_info: {user_info}')
        #! Use user info to authenticate or register the user
        email = user_info.get('email')
        if email:
            try:
                user = User.objects.get(username=email)
            except User.DoesNotExist:
                user = User.objects.create(username=email, auth_provider='google')
                user.set_unusable_password()
                user.save()
            
            if user:
                refresh = serializers.TokenObtainPairSerializer.get_token(user)
                data = {
                    'refresh_token': str(refresh),
                    'access_token': str(refresh.access_token)
                }
                return Response(data, status.HTTP_200_OK)
            
        return redirect('me')  # Redirect to your homepage or another page

class FacebookAuthView(generics.GenericAPIView):
    def get(self, request):
        client_id = settings.FACEBOOK_APP_ID
        redirect_uri = 'http://localhost:8000/callback/facebook/'
        scope = 'email'
        state = 'random_string_to_protect_against_csrf'
        
        authorization_url = 'https://www.facebook.com/v13.0/dialog/oauth'
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'state': state,
        }
        url = f"{authorization_url}?{urllib.parse.urlencode(params)}"
        return redirect(url)
    
class FacebookCallbackView(generics.GenericAPIView):
    def get(self, request):
        code = request.GET.get('code')
        if not code:
            return redirect('me')  # Handle the error case
        #! Use the code to get the access token
        token_url = 'https://graph.facebook.com/v13.0/oauth/access_token'
        data = {
            'client_id': settings.FACEBOOK_APP_ID,
            'redirect_uri': 'http://localhost:8000/callback/facebook/',
            'client_secret': settings.FACEBOOK_APP_SECRET,
            'code': code,
        }
        
        response = requests.get(token_url, params=data)
        token_response = response.json()
        
        if response.status_code == 200:
        #! Use the access token to get user info
            access_token = token_response.get('access_token')
            user_info_url = 'https://graph.facebook.com/me'
            params = {
                'fields': 'id,name,email',
                'access_token': access_token
            }
            response = requests.get(user_info_url, params=params)
            user_info = response.json()
            print (f'user_info: {user_info}')
        #! Use user info to authenticate or register the user
            email = user_info.get('email')
            if email:
                user, created = User.objects.get_or_create(username=email,auth_provider='facebook')
                if created:
                    user.set_unusable_password()  # or set a random password if needed
                    user.save()
                if user:
                    refresh = serializers.TokenObtainPairSerializer.get_token(user)
                    data = {
                        'refresh_token': str(refresh),
                        'access_token': str(refresh.access_token)
                    }
                    return Response(data, status.HTTP_200_OK)
        return redirect('me')  # Handle the error case
    





























#@ separate view for separated permissions
class UserManageView(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                UserSerializer,
                User.objects.filter(id=kwargs['pk'])
            )
            return Response(respn, status=respn['status'])
        else:
            respn = ViewUtils.paginated_get_response(
                self,
                request,
                UserSerializer,
                User.objects.all(),
            )
            return Response(respn, status=respn['status'])
    
    def post(self, request, *args, **kwargs):
        #* data : { [{ name, price, in_stock }] }
        items = request.data.get('items') if 'items' in request.data else [request.data]
        serializer_ = []
        for item in items:
            serializer = UserSerializer(data=item)
            if not serializer.is_valid():
                data = ViewUtils.gen_response(data=serializer.errors)
                return Response(data, data['status'])
            serializer_.append(serializer)
        try:
            [item.save() for item in serializer_]
        except Exception as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
            return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_201_CREATED, message='Users created successfully.', data=f'Users created: {len(serializer_)}')
        return Response(data=data, status=data['status'])
            
        
    def put(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='User id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = User.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='User not found.')
                    return Response(data, data['status'])
                serializer = UserSerializer(instance, data=item, partial=True)
                if not serializer.is_valid():
                    data = ViewUtils.gen_response(data=serializer.errors)
                    return Response(data, data['status'])
                serializer_.append(serializer)
        try:
            [item.save() for item in serializer_]
        except Exception as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
            return Response(data, data['status'])
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Users updated successfully.', data=f'Number of Users updated: {len(serializer_)}')
        return Response(data, status=data['status'])
    
    def patch(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='User must be provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            instance_ = []
            for item in items:
                instance = User.deleted.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='User not found or not deleted.')
                    return Response(data, data['status'])
                instance_.append(instance)
            try:
                [item.restore() for item in instance_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Users restored successfully.', data=f'Number of Users restored: {len(instance_)}')
            return Response(data, data['status'])
    
    def delete(self, request, *args, **kwargs):
        if 'pk' in kwargs and 'items' in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Please decide only 1 way to inform the id at a time.')
            return Response(data, data['status'])
        elif 'pk' not in kwargs and 'items' not in request.data:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='User id not provided.')
            return Response(data, data['status'])
        
        else:
            items = request.data.get('items') if 'items' in request.data else [{ 'id': kwargs['pk'], **request.data }]
            serializer_ = []
            for item in items:
                instance = User.objects.filter(id=item['id']).first()
                if not instance:
                    data = ViewUtils.gen_response(success=False, status=HTTP_404_NOT_FOUND, message='User not found.')
                    return Response(data, data['status'])
                serializer = UserSerializer(instance)
                serializer_.append(serializer)
                
            try:
                [item.delete() for item in serializer_]
            except Exception as e:
                data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='An error occurred while making changes.', data=str(e))
                return Response(data, data['status'])
            data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Users deleted successfully.', data=f'Number of Users deleted: {len(serializer_)}')
            return Response(data, data['status'])