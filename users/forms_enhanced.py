from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
import re

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        }),
        help_text="We'll never share your email with anyone else."
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name',
            'autocomplete': 'family-name'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number',
            'autocomplete': 'tel'
        }),
        help_text="Enter a valid phone number (10-15 digits)."
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your complete address',
            'rows': 3,
            'autocomplete': 'street-address'
        }),
        required=True,
        help_text="Enter your complete delivery address."
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username',
                'autocomplete': 'username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes and improve help text
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a strong password',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        })
        
        # Improve help text
        self.fields['password1'].help_text = (
            "Your password must contain at least 8 characters, "
            "include both letters and numbers, and not be too common."
        )
        self.fields['password2'].help_text = "Enter the same password as before, for verification."

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                raise ValidationError(
                    "An account with this email address already exists. "
                    "Please use a different email or try logging in."
                )
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove all non-digit characters
            digits_only = re.sub(r'[^\d]', '', phone)
            
            # Check length
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise ValidationError(
                    "Phone number must be between 10 and 15 digits long."
                )
            
            # Check if it's all the same digit (like 1111111111)
            if len(set(digits_only)) == 1:
                raise ValidationError(
                    "Please enter a valid phone number."
                )
            
            # Check if phone number already exists
            if User.objects.filter(phone_number=phone).exists():
                raise ValidationError(
                    "An account with this phone number already exists."
                )
            
        return phone

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check username pattern (alphanumeric and underscores only)
            if not re.match(r'^[a-zA-Z0-9_]+$', username):
                raise ValidationError(
                    "Username can only contain letters, numbers, and underscores."
                )
            
            # Check minimum length
            if len(username) < 3:
                raise ValidationError(
                    "Username must be at least 3 characters long."
                )
                
        return username

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            # Use Django's built-in password validators
            validate_password(password1)
            
            # Additional custom validations
            if len(password1) < 8:
                raise ValidationError(
                    "Password must be at least 8 characters long."
                )
            
            if not re.search(r'[A-Za-z]', password1):
                raise ValidationError(
                    "Password must contain at least one letter."
                )
            
            if not re.search(r'[0-9]', password1):
                raise ValidationError(
                    "Password must contain at least one number."
                )
                
        return password1

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.address = self.cleaned_data['address']
        
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email',
            'autocomplete': 'username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = "Enter your username or email address."
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and '@' in username:
            # If it looks like an email, try to find user by email
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                pass
        return username

    error_messages = {
        'invalid_login': (
            "Please enter a correct username/email and password. "
            "Note that both fields may be case-sensitive."
        ),
        'inactive': "This account is inactive.",
    }


class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        }),
        help_text="Enter the email address associated with your account."
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if not User.objects.filter(email=email).exists():
                raise ValidationError(
                    "No account found with this email address."
                )
        return email


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Address',
                'rows': 3
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and self.instance:
            # Check if email is changed and if it already exists
            if (email != self.instance.email and 
                User.objects.filter(email=email).exists()):
                raise ValidationError(
                    "An account with this email address already exists."
                )
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove all non-digit characters
            digits_only = re.sub(r'[^\d]', '', phone)
            
            # Check length
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise ValidationError(
                    "Phone number must be between 10 and 15 digits long."
                )
            
            # Check if phone number is changed and if it already exists
            if (phone != self.instance.phone_number and 
                User.objects.filter(phone_number=phone).exists()):
                raise ValidationError(
                    "An account with this phone number already exists."
                )
            
        return phone