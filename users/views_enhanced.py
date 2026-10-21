from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
import logging

from .forms_enhanced import CustomUserCreationForm, CustomAuthenticationForm, ProfileUpdateForm
from .models import CustomUser

logger = logging.getLogger(__name__)

class CustomLoginView(LoginView):
    """Enhanced login view with rate limiting and security features."""
    form_class = CustomAuthenticationForm
    template_name = 'users/login.html'
    success_url = reverse_lazy('store:home')
    
    @ratelimit(key='ip', rate='5/m', method='POST', block=True)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Security logging for successful logins."""
        user = form.get_user()
        logger.info(f"Successful login for user: {user.username} from IP: {self.request.META.get('REMOTE_ADDR')}")
        
        # Clear any existing messages before login
        storage = messages.get_messages(self.request)
        storage.used = True
        
        messages.success(self.request, f'Welcome back, {user.first_name or user.username}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Security logging for failed login attempts."""
        username = form.cleaned_data.get('username', 'Unknown')
        logger.warning(f"Failed login attempt for username: {username} from IP: {self.request.META.get('REMOTE_ADDR')}")
        
        # Clear any existing messages
        storage = messages.get_messages(self.request)
        storage.used = True
        
        messages.error(self.request, 'Invalid username/email or password. Please try again.')
        return super().form_invalid(form)


@ratelimit(key='ip', rate='3/m', method='POST', block=True)
@require_http_methods(["GET", "POST"])
def signup_view(request):
    """Enhanced signup view with comprehensive validation and security."""
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('store:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        
        # Clear any existing messages
        storage = messages.get_messages(request)
        storage.used = True
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    
                    # Log successful registration
                    logger.info(f"New user registered: {user.username} ({user.email}) from IP: {request.META.get('REMOTE_ADDR')}")
                    
                    # Authenticate and login the user
                    username = form.cleaned_data.get('username')
                    password = form.cleaned_data.get('password1')
                    user = authenticate(username=username, password=password)
                    
                    if user is not None:
                        login(request, user)
                        messages.success(
                            request, 
                            f'Welcome to PharmaCure, {user.first_name}! Your account has been created successfully.'
                        )
                        
                        # Redirect to home page after successful signup
                        return redirect('store:home')
                    else:
                        messages.error(request, 'Account created but login failed. Please try logging in manually.')
                        return redirect('users:login')
                        
            except ValidationError as e:
                logger.error(f"Validation error during signup: {e}")
                messages.error(request, 'Please correct the errors below.')
            except Exception as e:
                logger.error(f"Unexpected error during signup: {e}")
                messages.error(request, 'An unexpected error occurred. Please try again.')
        else:
            # Form has validation errors
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        error_messages.append(str(error))
                    else:
                        field_label = form.fields[field].label or field.replace('_', ' ').title()
                        error_messages.append(f"{field_label}: {error}")
            
            if error_messages:
                messages.error(request, ' | '.join(error_messages[:3]))  # Show max 3 errors
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/signup.html', {'form': form})


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    """User profile view with update functionality."""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        
        # Clear any existing messages
        storage = messages.get_messages(request)
        storage.used = True
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    logger.info(f"Profile updated for user: {request.user.username}")
                    messages.success(request, 'Your profile has been updated successfully!')
                    return redirect('users:profile')
            except Exception as e:
                logger.error(f"Error updating profile for user {request.user.username}: {e}")
                messages.error(request, 'An error occurred while updating your profile.')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    field_label = form.fields[field].label or field.replace('_', ' ').title()
                    error_messages.append(f"{field_label}: {error}")
            
            if error_messages:
                messages.error(request, ' | '.join(error_messages[:3]))
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'users/profile.html', {'form': form})


@login_required
@require_http_methods(["GET"])
def dashboard_view(request):
    """User dashboard with order history and account summary."""
    try:
        # Get user's recent orders
        from store.models import Order
        recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
        
        # Calculate statistics
        total_orders = Order.objects.filter(user=request.user).count()
        total_spent = sum(order.total_amount for order in Order.objects.filter(user=request.user))
        
        context = {
            'recent_orders': recent_orders,
            'total_orders': total_orders,
            'total_spent': total_spent,
        }
        
        return render(request, 'users/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error loading dashboard for user {request.user.username}: {e}")
        messages.error(request, 'Unable to load dashboard. Please try again.')
        return redirect('store:home')


@require_http_methods(["POST"])
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def check_email_availability(request):
    """AJAX endpoint to check email availability during registration."""
    email = request.POST.get('email')
    
    if not email:
        return JsonResponse({'available': False, 'message': 'Email is required.'})
    
    try:
        exists = CustomUser.objects.filter(email=email).exists()
        if exists:
            return JsonResponse({
                'available': False, 
                'message': 'This email is already registered.'
            })
        else:
            return JsonResponse({
                'available': True, 
                'message': 'Email is available.'
            })
    except Exception as e:
        logger.error(f"Error checking email availability: {e}")
        return JsonResponse({
            'available': False, 
            'message': 'Unable to verify email. Please try again.'
        })


@require_http_methods(["POST"])
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def check_username_availability(request):
    """AJAX endpoint to check username availability during registration."""
    username = request.POST.get('username')
    
    if not username:
        return JsonResponse({'available': False, 'message': 'Username is required.'})
    
    try:
        exists = CustomUser.objects.filter(username=username).exists()
        if exists:
            return JsonResponse({
                'available': False, 
                'message': 'This username is already taken.'
            })
        else:
            return JsonResponse({
                'available': True, 
                'message': 'Username is available.'
            })
    except Exception as e:
        logger.error(f"Error checking username availability: {e}")
        return JsonResponse({
            'available': False, 
            'message': 'Unable to verify username. Please try again.'
        })


@login_required
@require_http_methods(["POST"])
def delete_account_view(request):
    """Secure account deletion with confirmation."""
    password = request.POST.get('password')
    
    if not password:
        messages.error(request, 'Password is required to delete your account.')
        return redirect('users:profile')
    
    # Verify password
    if not request.user.check_password(password):
        messages.error(request, 'Incorrect password. Account deletion cancelled.')
        return redirect('users:profile')
    
    try:
        with transaction.atomic():
            username = request.user.username
            request.user.delete()
            
            logger.info(f"Account deleted for user: {username}")
            messages.success(request, 'Your account has been permanently deleted.')
            
        return redirect('store:home')
        
    except Exception as e:
        logger.error(f"Error deleting account for user {request.user.username}: {e}")
        messages.error(request, 'Unable to delete account. Please contact support.')
        return redirect('users:profile')


@never_cache
def health_check(request):
    """Health check endpoint for monitoring."""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })