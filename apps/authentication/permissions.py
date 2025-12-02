from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """Allow access only to owner or admin"""
    
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.is_staff:
            return True
        
        # Check if object has user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object is the user itself
        return obj == request.user

class HasSubscriptionAccess(permissions.BasePermission):
    """Check if user has required subscription tier"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Get required tier from view
        required_tier = getattr(view, 'required_subscription_tier', 'basic')
        
        # Check user's subscription tier
        user_tier = request.user.profile.subscription_tier
        
        tier_hierarchy = {'basic': 1, 'premium': 2, 'pro': 3}
        
        return tier_hierarchy.get(user_tier, 0) >= tier_hierarchy.get(required_tier, 0)
