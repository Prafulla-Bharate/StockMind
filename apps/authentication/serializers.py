from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserProfile


class UserSerializer(serializers.ModelSerializer):
    # expose camelCase fields expected by frontend and map to model fields
    fullName = serializers.CharField(source='full_name', read_only=True)
    avatarUrl = serializers.CharField(source='avatar_url', read_only=True, allow_null=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'fullName', 'avatarUrl', 'createdAt']
        read_only_fields = ['id', 'createdAt']


class RegisterSerializer(serializers.ModelSerializer):
    # accept camelCase input from frontend: fullName
    fullName = serializers.CharField(write_only=True, source='full_name', required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['email', 'password', 'fullName']

    def create(self, validated_data):
        # validated_data will have {'email':..., 'password':..., 'full_name': ...}
        email = validated_data.get('email')
        password = validated_data.get('password')
        full_name = validated_data.get('full_name')

        # Create the user. A UserProfile is created by the post_save signal
        # in `apps.authentication.signals.create_user_profile`, so avoid
        # creating it here to prevent duplicate-key errors.
        user = User.objects.create_user(email=email, password=password, full_name=full_name)
        return user

    def to_internal_value(self, data):
        # Be tolerant: accept either camelCase (`fullName`) or snake_case (`full_name`).
        if isinstance(data, dict):
            # If frontend sent snake_case, map it to the serializer field names
            if 'full_name' in data and 'fullName' not in data:
                data['fullName'] = data.get('full_name')
        return super().to_internal_value(data)


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
    # accept camelCase fields for updates
    fullName = serializers.CharField(source='full_name', required=False)
    avatarUrl = serializers.CharField(source='avatar_url', required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['fullName', 'avatarUrl']

    def update(self, instance, validated_data):
        # validated_data uses model field names due to `source`
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.avatar_url = validated_data.get('avatar_url', instance.avatar_url)
        instance.save()
        return instance

    def to_internal_value(self, data):
        # Accept both camelCase and snake_case input for profile updates.
        if isinstance(data, dict):
            if 'full_name' in data and 'fullName' not in data:
                data['fullName'] = data.get('full_name')
            if 'avatar_url' in data and 'avatarUrl' not in data:
                data['avatarUrl'] = data.get('avatar_url')
        return super().to_internal_value(data)

