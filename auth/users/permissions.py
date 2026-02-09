from rest_framework.permissions import IsAuthenticated, BasePermission
# Импортируем из того же места, что и в настройках
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope 

class OAuthOrJWT(BasePermission):
    oauth_permission = TokenHasReadWriteScope()

    def has_permission(self, request, view) -> bool:
        if not IsAuthenticated().has_permission(request, view):
            return False
        if hasattr(request, 'oauth2_provider_token'):
            return self.oauth_permission.has_permission(request, view)
        return True