from rest_framework.permissions import BasePermission, IsAdminUser, IsAuthenticated

class IsMerchant(BasePermission):
    """
    Allows access only to authorized merchant.
    """
    def has_permission(self, request, view):
        return bool(request.user and (request.user.is_merchant or request.user.is_staff))