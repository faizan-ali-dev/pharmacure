from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'required': True
        }),
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Please enter a valid email address.',
        }
    )
    
    street = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your street address',
            'required': True
        }),
        error_messages={
            'required': 'Street address is required.',
        }
    )
    
    city = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your city',
            'required': True
        }),
        error_messages={
            'required': 'City is required.',
        }
    )
    
    phone_number = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number',
            'required': True
        }),
        error_messages={
            'required': 'Phone number is required.',
        }
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'street', 'city', 'phone_number', 'password1', 'password2')
        error_messages = {
            'username': {
                'required': 'Username is required.',
                'unique': 'This username is already taken. Please choose another.',
            },
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username',
            'required': True
        })
        self.fields['username'].error_messages.update({
            'required': 'Username is required.',
            'unique': 'This username is already taken. Please choose another.',
        })
        
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your first name',
            'required': True
        })
        self.fields['first_name'].error_messages.update({
            'required': 'First name is required.',
        })
        self.fields['first_name'].required = True
        
        self.fields['last_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your last name',
            'required': True
        })
        self.fields['last_name'].error_messages.update({
            'required': 'Last name is required.',
        })
        self.fields['last_name'].required = True
        
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a strong password',
            'required': True
        })
        self.fields['password1'].error_messages.update({
            'required': 'Password is required.',
        })
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'required': True
        })
        self.fields['password2'].error_messages.update({
            'required': 'Please confirm your password.',
        })

    def clean_email(self):
        """Check if email is already registered"""
        email = self.cleaned_data.get('email')
        if email:
            if CustomUser.objects.filter(email=email).exists():
                raise ValidationError(
                    'An account with this email address already exists. '
                    'Please use a different email or try logging in.'
                )
        return email

    def clean_phone_number(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone_number')
        if phone:
            cleaned_phone = ''.join(filter(str.isdigit, phone))
            if len(cleaned_phone) < 10:
                raise ValidationError('Please enter a valid phone number with at least 10 digits.')
            if len(cleaned_phone) > 15:
                raise ValidationError('Phone number is too long. Please enter a valid phone number.')
        return phone

    def clean_username(self):
        """Additional username validation"""
        username = self.cleaned_data.get('username')
        if username:
            if len(username) < 3:
                raise ValidationError('Username must be at least 3 characters long.')
            if not username.replace('_', '').replace('.', '').isalnum():
                raise ValidationError('Username can only contain letters, numbers, underscores, and periods.')
        return username


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
        self.fields['username'].error_messages.update({
            'required': 'Username is required.',
        })
        
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
        self.fields['password'].error_messages.update({
            'required': 'Password is required.',
        })

    def clean(self):
        """Enhanced authentication with single clear error message"""
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            
            if self.user_cache is None:
                raise ValidationError(
                    'Invalid username or password. Please check your credentials and try again.'
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
