from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from .forms import UserRegistrationForm, UserLoginForm
from .utils import get_client_ip
import logging

logger = logging.getLogger(__name__)

class UserRegistrationView(View):
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = UserRegistrationForm()
        return render(request, 'user_management/register.html', {'form': form})

    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                logger.info(f"New patient registered: {user.email} from IP: {get_client_ip(request)}")
                messages.success(request, 'Registration successful.')
                return redirect('patient_dashboard')
            except Exception as e:
                logger.error(f"Unexpected error during registration: {str(e)}")
                messages.error(request, "An unexpected error occurred. Please try again later.")
        else:
            logger.warning(f"Registration failed for email: {request.POST.get('email')} from IP: {get_client_ip(request)}. Errors: {form.errors}")
        return render(request, 'user_management/register.html', {'form': form})

class UserLoginView(View):
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        if request.user.is_authenticated:
            return self.redirect_based_on_role(request.user)
        form = UserLoginForm()
        return render(request, 'user_management/login.html', {'form': form})

    def post(self, request):
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                logger.info(f"User logged in: {user.email} (Role: {user.role}) from IP: {get_client_ip(request)}")
                messages.success(request, 'Login successful.')
                return self.redirect_based_on_role(user)
            else:
                logger.warning(f"Failed login attempt for email: {email} from IP: {get_client_ip(request)}")
                messages.error(request, "Invalid email or password.")
        else:
            logger.warning(f"Login form invalid for IP: {get_client_ip(request)}. Errors: {form.errors}")
        return render(request, 'user_management/login.html', {'form': form})

    def redirect_based_on_role(self, user):
        return redirect('dashboard')

def user_logout(request):
    if request.user.is_authenticated:
        logger.info(f"User logged out: {request.user.email} (Role: {request.user.role}) from IP: {get_client_ip(request)}")
        logout(request)
        messages.success(request, 'You have been logged out.')
    return redirect('login')