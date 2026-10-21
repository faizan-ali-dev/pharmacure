from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinLengthValidator
from django.utils import timezone


class CustomUser(AbstractUser):
    """Enhanced user model with additional fields and validation."""
    
    email = models.EmailField(
        unique=True,
        help_text="Required. Enter a valid email address."
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        unique=True,
        help_text="Enter phone number in format: +1234567890"
    )
    
    address = models.TextField(
        max_length=500,
        help_text="Complete delivery address"
    )
    
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="Optional: Enter your date of birth"
    )
    
    # Account security fields
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether email address has been verified"
    )
    
    phone_verified = models.BooleanField(
        default=False,
        help_text="Whether phone number has been verified"
    )
    
    failed_login_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Number of consecutive failed login attempts"
    )
    
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of last successful login"
    )
    
    account_locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Account locked until this timestamp"
    )
    
    # Profile fields
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        help_text="Optional profile picture"
    )
    
    preferred_language = models.CharField(
        max_length=10,
        choices=[
            ('en', 'English'),
            ('ur', 'Urdu'),
            ('hi', 'Hindi'),
        ],
        default='en',
        help_text="Preferred language for communications"
    )
    
    newsletter_subscription = models.BooleanField(
        default=True,
        help_text="Receive newsletter and promotional emails"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_profile_update = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['created_at']),
            models.Index(fields=['last_login']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})" if self.get_full_name() else self.username
    
    def get_full_name(self):
        """Return full name or username if names not provided."""
        full_name = super().get_full_name()
        return full_name if full_name.strip() else self.username
    
    def is_account_locked(self):
        """Check if account is currently locked."""
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False
    
    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration."""
        self.account_locked_until = timezone.now() + timezone.timedelta(minutes=duration_minutes)
        self.save(update_fields=['account_locked_until'])
    
    def unlock_account(self):
        """Unlock account and reset failed attempts."""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
    
    def increment_failed_login(self):
        """Increment failed login attempts and lock if threshold reached."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
            self.lock_account(30)  # Lock for 30 minutes
        self.save(update_fields=['failed_login_attempts'])
    
    def reset_failed_login(self):
        """Reset failed login attempts on successful login."""
        if self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            self.save(update_fields=['failed_login_attempts'])
    
    def get_display_name(self):
        """Get display name for UI."""
        if self.first_name:
            return self.first_name
        return self.username
    
    def save(self, *args, **kwargs):
        """Override save to ensure email is lowercase."""
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)