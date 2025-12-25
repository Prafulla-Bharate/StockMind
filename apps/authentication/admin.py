from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'is_active', 'is_staff', 'is_email_verified', 'created_at']
    list_filter = ['is_active', 'is_staff', 'is_email_verified', 'created_at']
    search_fields = ['email', 'full_name']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Identity', {'fields': ('email', 'full_name', 'avatar_url')}),
        ('Verification', {'fields': ('is_email_verified',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    filter_horizontal = ('groups', 'user_permissions')
    ordering = ['-created_at']
