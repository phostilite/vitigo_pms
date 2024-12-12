import logging
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from error_handling.views import (
    handler400, handler401, handler403, handler404, handler500
)
from .forms import UserLoginForm

# Configure logger
logger = logging.getLogger(__name__)

class UserLoginView(View):
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        try:
            if request.user.is_authenticated:
                messages.info(request, f'You are already logged in as {request.user.email}')
                return redirect('dashboard')
            form = UserLoginForm()
            return render(request, 'user_management/login.html', {'form': form})
        except Exception as e:
            logger.error(f"Error in login GET: {str(e)}")
            messages.error(request, 'An error occurred while accessing the login page')
            return handler500(request, exception=e)

    def post(self, request):
        try:
            form = UserLoginForm(request.POST)
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                return handler400(request, exception="Please correct the errors in the form")

            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)

            if not user:
                messages.warning(request, 'Invalid email or password. Please try again.')
                return handler401(request, exception="Authentication failed")

            if not user.is_active:
                messages.warning(request, 'Your account is inactive. Please contact support.')
                return handler403(request, exception="Account inactive")

            login(request, user)
            logger.info(f"User logged in successfully: {email}")
            messages.success(request, f'Welcome back, {user.get_full_name() or user.email}!')
            return redirect('dashboard')

        except ValueError as e:
            messages.error(request, f'Invalid input: {str(e)}')
            return handler400(request, exception=e)
        except Exception as e:
            messages.error(request, 'An unexpected error occurred. Please try again.')
            return handler500(request, exception=e)

class UserLogoutView(LoginRequiredMixin, View):
    """Handle user logout with proper error handling and logging"""
    
    def get(self, request):
        try:
            user_email = request.user.email
            user_name = request.user.get_full_name() or user_email
            user_role = request.user.role
            logout(request)
            logger.info(f"User logged out: {user_email} (Role: {user_role})")
            messages.success(request, f'Goodbye, {user_name}! You have been logged out successfully.')
            return redirect('login')
        except AttributeError as e:
            messages.error(request, 'Invalid session. Please try logging in again.')
            return handler400(request, exception="Session error")
        except Exception as e:
            messages.error(request, 'An error occurred during logout.')
            return handler500(request, exception=e)