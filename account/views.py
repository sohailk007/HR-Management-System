
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Accounts
from .jwt_utils import JWTHandler
import re

@csrf_protect
def register_view(request):
    """
    User registration view
    """
    if request.method == 'POST':
        try:
            # Get form data
            salutation = request.POST.get('salutation')
            full_name = request.POST.get('full_name')
            dob = request.POST.get('dob')
            gender = request.POST.get('gender')
            username = request.POST.get('username').lower().strip()
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            location = request.POST.get('location')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            
            
            # Validation
            errors = []
            
            # Check if username already exists
            if Accounts.objects.filter(username=username).exists():
                errors.append("An account with this username already exists.")
                
            # Check if username is already exists
            if Accounts.objects.filter(phone=phone).exists():
                errors.append("An account with this phone number already exists.")
            
            # Validate password match
            if password != password_confirm:
                errors.append("Passwords do not match.")
            
            # Validate password strength
            try:
                validate_password(password)
            except ValidationError as e:
                errors.extend(list(e.messages))
            
            # Check required fields
            required_fields = {
                'full_name': full_name,
                'dob': dob,
                'gender': gender,
                'username': username,
                'address': address,
                'location': location,
            }
            
            for field, value in required_fields.items():
                if not value:
                    errors.append(f"{field.replace('_', ' ').title()} is required.")
            
            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'register.html', {'form_data': request.POST})
            
            # Create account
            account = Accounts(
                salutation=salutation,
                full_name=full_name,
                dob=dob,
                gender=gender,
                username=username,
                phone=phone,
                address=address,
                location=location
            )
            account.set_password(password)
            account.save()
            
            messages.success(request, "Account created successfully! Please login.")
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'register.html', {'form_data': request.POST})
    
    return render(request, 'register.html')


@csrf_protect
def login_view(request):
    """
    User login view
    """
    # If already authenticated, redirect to dashboard
    if hasattr(request, 'is_authenticated') and request.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').lower().strip()
        password = request.POST.get('password', '')
        
        try:
            # Find account
            account = Accounts.objects.get(username=username)
            
            # Check if account is active
            if not account.is_active:
                messages.error(request, "Your account has been deactivated.")
                return render(request, 'login.html')
            
            # Verify password
            if account.check_password(password):
                # Generate tokens
                access_token = JWTHandler.generate_access_token(account)
                refresh_token = JWTHandler.generate_refresh_token(account)
                
                # Update last login
                account.last_login = timezone.now()
                account.save(update_fields=['last_login'])
                
                # Create response and set cookies
                response = redirect('dashboard')
                response.set_cookie(
                    'access_token',
                    access_token,
                    max_age=3600,  # 1 hour
                    httponly=True,
                    secure=False,  # Set to True in production with HTTPS
                    samesite='Lax'
                )
                response.set_cookie(
                    'refresh_token',
                    refresh_token,
                    max_age=604800,  # 7 days
                    httponly=True,
                    secure=False,  # Set to True in production with HTTPS
                    samesite='Lax'
                )
                
                messages.success(request, f"Welcome back, {account.full_name}!")
                return response
            else:
                messages.error(request, "Invalid username or password.")
                
        except Accounts.DoesNotExist:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'login.html')


def logout_view(request):
    """
    User logout view
    """
    # Blacklist refresh token
    refresh_token = request.COOKIES.get('refresh_token')
    if refresh_token:
        JWTHandler.blacklist_refresh_token(refresh_token)
    
    # Create response and delete cookies
    response = redirect('login')
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    
    messages.success(request, "You have been logged out successfully.")
    return response


def dashboard_view(request):
    """
    Dashboard view - requires authentication
    """
    account = request.user_account
    
    # Check if token needs refresh
    if hasattr(request, 'needs_token_refresh') and request.needs_token_refresh:
        # Generate new access token
        access_token = JWTHandler.generate_access_token(account)
        
        response = render(request, 'dashboard.html', {'account': account})
        response.set_cookie(
            'access_token',
            access_token,
            max_age=3600,
            httponly=True,
            secure=False,
            samesite='Lax'
        )
        return response
    
    return render(request, 'dashboard.html', {'account': account})


def profile_view(request):
    """
    User profile view
    """
    account = request.user_account
    return render(request, 'profile.html', {'account': account})


@csrf_protect
def change_password_view(request):
    """
    Change password view
    """
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password_confirm = request.POST.get('new_password_confirm')
        
        account = request.user_account
        
        # Validation
        errors = []
        
        # Check old password
        if not account.check_password(old_password):
            errors.append("Current password is incorrect.")
        
        # Check new password match
        if new_password != new_password_confirm:
            errors.append("New passwords do not match.")
        
        # Validate new password strength
        try:
            validate_password(new_password)
        except ValidationError as e:
            errors.extend(list(e.messages))
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'change_password.html')
        
        # Update password
        account.set_password(new_password)
        account.save()
        
        # Logout from all devices
        JWTHandler.blacklist_all_user_tokens(account)
        
        # Create response and delete cookies
        response = redirect('login')
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        
        messages.success(request, "Password changed successfully. Please login again.")
        return response
    
    return render(request, 'change_password.html')