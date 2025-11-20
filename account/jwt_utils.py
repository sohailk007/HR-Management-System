import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import Accounts, RefreshToken

class JWTHandler:
    """
    JWT Token Handler for authentication
    """
    
    @staticmethod
    def generate_access_token(account):
        """
        Generate access token for authenticated user
        """
        payload = {
            'user_id': str(account.id),
            'username': account.username,
            'exp': datetime.utcnow() + settings.JWT_ACCESS_TOKEN_LIFETIME,
            'iat': datetime.utcnow(),
            'token_type': 'access'
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token
    
    @staticmethod
    def generate_refresh_token(account):
        """
        Generate refresh token and store in database
        """
        payload = {
            'user_id': str(account.id),
            'exp': datetime.utcnow() + settings.JWT_REFRESH_TOKEN_LIFETIME,
            'iat': datetime.utcnow(),
            'token_type': 'refresh'
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        # Storing refresh token in database
        expires_at = timezone.now() + settings.JWT_REFRESH_TOKEN_LIFETIME
        RefreshToken.objects.create(
            account=account,
            token=token,
            expires_at=expires_at
        )
        
        return token
    
    @staticmethod
    def verify_access_token(token):
        """
        Verify and decode access token
        Returns account object if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            
            if payload.get('token_type') != 'access':
                return None
            
            account = Accounts.objects.get(id=payload['user_id'], is_active=True)
            return account
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Accounts.DoesNotExist:
            return None
    
    @staticmethod
    def verify_refresh_token(token):
        """
        Verify refresh token from database
        Returns account object if valid, None otherwise
        """
        try:
            # Check if token exists in database
            refresh_token = RefreshToken.objects.get(token=token, is_blacklisted=False)
            
            if refresh_token.is_expired():
                return None
            
            # Decode token
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            
            if payload.get('token_type') != 'refresh':
                return None
            
            account = Accounts.objects.get(id=payload['user_id'], is_active=True)
            return account
            
        except RefreshToken.DoesNotExist:
            return None
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Accounts.DoesNotExist:
            return None
    
    @staticmethod
    def blacklist_refresh_token(token):
        """
        Blacklist a refresh token (for logout)
        """
        try:
            refresh_token = RefreshToken.objects.get(token=token)
            refresh_token.is_blacklisted = True
            refresh_token.save()
            return True
        except RefreshToken.DoesNotExist:
            return False
    
    @staticmethod
    def blacklist_all_user_tokens(account):
        """
        Blacklist all refresh tokens for a user (logout from all devices)
        """
        RefreshToken.objects.filter(account=account, is_blacklisted=False).update(is_blacklisted=True)