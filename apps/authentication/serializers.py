from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserProfile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name',  'avatar_url','created_at']
        read_only_fields = ['id', 'created_at']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    full_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name']

        def create(self, validated_data):
            user = User.objects.create(
                email=validated_data['email'],
                password = validated_data['password'],
                full_name=validated_data['full_name']
            )

            UserProfile.objects.create(
                user=user,
                api_key = UserProfile.generate_api_key()
            )
            return user
        
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password.")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
        else:
            raise serializers.ValidationError("Both email and password are required.")
        
        attrs['user'] = user
        return attrs
    

class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['full_name', 'avatar_url']

    def update(self,instance, validated_data):
        instance.full_name = validated_data.get('full_name',instance.full_name)
        instance.avatar_url = validated_data.get('avatar_url',instance.avatar_url)
        instance.save()
        return instance
    
    