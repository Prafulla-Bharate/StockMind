import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string

class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom User model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(max_length=255)
    avatar_url = models.URLField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return self.email

class UserProfile(models.Model):
    """Extended user profile"""
    
    SUBSCRIPTION_CHOICES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('pro', 'Pro'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    subscription_tier = models.CharField(max_length=20, choices=SUBSCRIPTION_CHOICES, default='basic')
    api_key = models.CharField(max_length=64, unique=True)
    daily_request_count = models.IntegerField(default=0)
    max_daily_requests = models.IntegerField(default=1000)
    watchlist_limit = models.IntegerField(default=50)
    portfolio_limit = models.IntegerField(default=100)
    notification_preferences = models.JSONField(default=dict, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
    
    def __str__(self):
        return f"{self.user.email} - {self.subscription_tier}"
    
    def reset_daily_request_count(self):
        """Reset daily API request counter"""
        self.daily_request_count = 0
        self.save(update_fields=['daily_request_count'])
    
    def increment_request_count(self):
        """Increment API request counter"""
        self.daily_request_count += 1
        self.save(update_fields=['daily_request_count'])
    
    @staticmethod
    def generate_api_key():
        """Generate unique API key"""
        return get_random_string(64)

class RefreshToken(models.Model):
    """Store refresh tokens for JWT"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens')
    token = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'refresh_tokens'
        verbose_name = _('refresh token')
        verbose_name_plural = _('refresh tokens')
        indexes = [
            models.Index(fields=['user', 'is_revoked']),
            models.Index(fields=['token']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.created_at}"
    
    def revoke(self):
        """Revoke this token"""
        self.is_revoked = True
        self.save(update_fields=['is_revoked'])