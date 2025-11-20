from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password, check_password
from datetime import date
import uuid

class Accounts(models.Model):
    """
    Enhanced Account model for user registration with JWT authentication
    """
    # Salutation choices
    SALUTATION_CHOICES = [
        ("Mr", "Mr"),
        ("Miss", "Miss"),
    ]
    
    # Gender choices
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]
    
    # Phone number validator
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )
    
    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Authentication Fields
    username = models.CharField(
        unique=True,
        max_length=100,
        verbose_name="username",
        help_text="Enter your username",
        db_index=True,
    )
    password = models.CharField(max_length=255, verbose_name="Password")
    
    # Personal Information Fields
    salutation = models.CharField(
        max_length=10,
        choices=SALUTATION_CHOICES,
        default="Mr",
        verbose_name="Salutation",
    )
    full_name = models.CharField(
        max_length=100, verbose_name="Full Name", help_text="Enter your full name"
    )
    dob = models.DateField(verbose_name="Date of Birth", help_text="Format: YYYY-MM-DD")
    gender = models.CharField(
        max_length=1, choices=GENDER_CHOICES, verbose_name="Gender"
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True,
        verbose_name="Phone Number",
        help_text="Enter phone number with country code",
    )
    address = models.TextField(
        verbose_name="Address", help_text="Enter your complete address"
    )
    location = models.CharField(max_length=100, verbose_name="City/Location")
    
    # Account Status
    is_active = models.BooleanField(default=True, verbose_name="Active Status")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        return f"{self.get_salutation_display()} {self.full_name}"
    
    def set_password(self, raw_password):
        """Hash and set the password"""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check if the provided password is correct"""
        return check_password(raw_password, self.password)
    
    def get_full_display_name(self):
        """Returns full name with salutation"""
        return f"{self.get_salutation_display()} {self.full_name}"
    
    def get_age(self):
        """Calculate age from date of birth"""
        today = date.today()
        return (
            today.year
            - self.dob.year
            - ((today.month, today.day) < (self.dob.month, self.dob.day))
        )


class RefreshToken(models.Model):
    """
    Model to store refresh tokens for JWT authentication
    """
    account = models.ForeignKey(Accounts, on_delete=models.CASCADE, related_name='refresh_tokens')
    token = models.CharField(max_length=500, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_blacklisted = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Refresh Token"
        verbose_name_plural = "Refresh Tokens"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Token for {self.account.username}"
    
    def is_expired(self):
        """Check if token is expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
