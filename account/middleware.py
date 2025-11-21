from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from .jwt_utils import JWTHandler

class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to authenticate users using JWT tokens stored in cookies
    """
    
    def process_request(self, request):
        """
        Process each request and authenticate user if valid token exists
        """
        # Skip authentication for static files and public URLs
        public_urls = [
            reverse('login'),
            reverse('register'),
            reverse('home'),
            '/static/',
            '/media/',
        ]
        
        # Check if current path is public
        is_public = any(request.path.startswith(url) for url in public_urls)
        
        # Get access token from cookie
        access_token = request.COOKIES.get('access_token')
        
        if access_token:
            # Verify access token
            account = JWTHandler.verify_access_token(access_token)
            
            if account:
                # Attach account to request
                request.user_account = account
                request.is_authenticated = True
            else:
                # Try to refresh token
                refresh_token = request.COOKIES.get('refresh_token')
                
                if refresh_token:
                    account = JWTHandler.verify_refresh_token(refresh_token)
                    
                    if account:
                        request.user_account = account
                        request.is_authenticated = True
                        request.needs_token_refresh = True
                    else:
                        request.user_account = None
                        request.is_authenticated = False
                else:
                    request.user_account = None
                    request.is_authenticated = False
        else:
            request.user_account = None
            request.is_authenticated = False
        
        # Redirect to login if not authenticated and trying to access protected page
        if not is_public and not request.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        
        return None