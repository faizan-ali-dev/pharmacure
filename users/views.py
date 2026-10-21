from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from .forms import CustomUserCreationForm, CustomAuthenticationForm


def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        try:
            if form.is_valid():
                user = form.save()
                login(request, user)
                messages.success(
                    request, 
                    f'Welcome {user.first_name}! Your account has been created successfully.'
                )
                return redirect('store:home')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)
        except IntegrityError as e:
            messages.error(
                request, 
                'An account with this information already exists. Please check your details.'
            )
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(
                request, 
                'An unexpected error occurred. Please try again later.'
            )
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/signup.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    authentication_form = CustomAuthenticationForm
    
    def get_success_url(self):
        messages.success(
            self.request, 
            f'Welcome back! You have been logged in successfully.'
        )
        return '/'  # Redirect to home page after login
    
    def form_invalid(self, form):
        """Handle form errors with single clear message"""
        storage = messages.get_messages(self.request)
        storage.used = True
        
        messages.error(
            self.request, 
            'Invalid username or password. Please check your credentials and try again.'
        )
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)
    
    next_page = 'store:home'
