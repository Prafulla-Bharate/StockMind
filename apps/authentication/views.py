from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    RegisterSerializer, 
    LoginSerializer, 
    UserSerializer,
    ProfileUpdateSerializer
)
from utils.responses import success_response, error_response

User = get_user_model()

class RegisterView(APIView):
    """User registration endpoint"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """POST /api/auth/register"""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response(success_response(
                data={
                    'token': str(refresh.access_token),
                    'user': UserSerializer(user).data
                },
                message='Registration successful'
            ), status=status.HTTP_201_CREATED)
        
        return Response(error_response(
            message='Registration failed',
            errors=serializer.errors
        ), status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """User login endpoint"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """POST /api/auth/login"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Update profile
            if hasattr(user, 'profile'):
                profile = user.profile
                profile.last_login_ip = request.META.get('REMOTE_ADDR')
                profile.save(update_fields=['last_login_ip'])
            
            return Response(success_response(
                data={
                    'token': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserSerializer(user).data
                },
                message='Login successful'
            ), status=status.HTTP_200_OK)
        
        return Response(error_response(
            message='Login failed',
            errors=serializer.errors
        ), status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    """User logout endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """POST /api/auth/logout"""
        try:
            # Revoke refresh tokens
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response(success_response(
                message='Logout successful'
            ), status=status.HTTP_200_OK)
        except Exception as e:
            return Response(error_response(
                message='Logout failed',
                errors={'detail': str(e)}
            ), status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    """User profile endpoint"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """GET /api/auth/profile"""
        user = request.user
        return Response(success_response(
            data=UserSerializer(user).data
        ), status=status.HTTP_200_OK)
    
    def patch(self, request):
        """PATCH /api/auth/profile"""
        user = request.user
        serializer = ProfileUpdateSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(success_response(
                data=UserSerializer(user).data,
                message='Profile updated successfully'
            ), status=status.HTTP_200_OK)
        
        return Response(error_response(
            message='Profile update failed',
            errors=serializer.errors
        ), status=status.HTTP_400_BAD_REQUEST)