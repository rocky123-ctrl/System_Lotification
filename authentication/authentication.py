from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.core.cache import cache
from django.conf import settings

class InactivityJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication that enforces a rolling inactivity timeout.
    If the user hasn't made a request within the timeframe, their session is evaluated as expired.
    """
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user, token = result
            
            cache_key = f'last_activity_{user.id}'
            is_active = cache.get(cache_key)
            
            if not is_active:
                raise AuthenticationFailed(
                    detail='Sesión expirada por inactividad', 
                    code='inactivity_timeout'
                )
            
            # Restart the inactivity timer
            timeout_seconds = getattr(settings, 'INACTIVITY_TIMEOUT_SECONDS', 1200)  # 20 min default
            cache.set(cache_key, True, timeout=timeout_seconds)
            
        return result
