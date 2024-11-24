from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from .forms import UserRegistrationForm, UserLoginForm, UserCreationForm
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from user_management.models import CustomUser
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from doctor_management.models import DoctorProfile, Specialization, TreatmentMethodSpecialization, BodyAreaSpecialization, AssociatedConditionSpecialization
from patient_management.models import Patient, MedicalHistory
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from access_control.models import Role

logger = logging.getLogger(__name__)

def get_template_path(base_template, role, module=''):
    """
    Resolves template path based on user role.
    Now uses the template_folder from Role model.
    """
    if isinstance(role, Role):
        role_folder = role.template_folder
    else:
        # Fallback for any legacy code
        role = Role.objects.get(name=role)
        role_folder = role.template_folder
    
    if module:
        return f'dashboard/{role_folder}/{module}/{base_template}'
    return f'dashboard/{role_folder}/{base_template}'

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
                logger.info(f"New patient registered: {user.email}.")
                messages.success(request, 'Registration successful.')
                return redirect('patient_dashboard')
            except Exception as e:
                logger.error(f"Unexpected error during registration: {str(e)}")
                messages.error(request, "An unexpected error occurred. Please try again later.")
        else:
            logger.warning(f"Registration failed for email: {request.POST.get('email')}. Errors: {form.errors}")
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
                logger.info(f"User logged in: {user.email} (Role: {user.role}).")
                messages.success(request, 'Login successful.')
                return self.redirect_based_on_role(user)
            else:
                logger.warning(f"Failed login attempt for email: {email}.")
                messages.error(request, "Invalid email or password.")
        else:
            logger.warning(f"Login form invalid. Errors: {form.errors}")
        return render(request, 'user_management/login.html', {'form': form})

    def redirect_based_on_role(self, user):
        """
        Redirects user to appropriate dashboard based on their role
        """
        try:
            # Default fallback dashboard
            default_dashboard = 'dashboard'
            
            # Get role-based redirects
            role_redirects = {
                'SUPER_ADMIN': 'admin_dashboard',
                'ADMIN': 'admin_dashboard',
                'MANAGER': 'admin_dashboard',
                'DOCTOR': 'doctor_dashboard',
                'NURSE': 'nurse_dashboard',
                'MEDICAL_ASSISTANT': 'medical_dashboard',
                'RECEPTIONIST': 'reception_dashboard',
                'PHARMACIST': 'pharmacy_dashboard',
                'LAB_TECHNICIAN': 'lab_dashboard',
                'BILLING_STAFF': 'billing_dashboard',
                'INVENTORY_MANAGER': 'inventory_dashboard',
                'HR_STAFF': 'hr_dashboard',
                'SUPPORT_MANAGER': 'support_dashboard',
                'SUPPORT_STAFF': 'support_dashboard'
            }
            
            # Get the dashboard based on user's role name
            if user.role and hasattr(user.role, 'name'):
                return redirect(role_redirects.get(user.role.name, default_dashboard))
            
            # Fallback to default dashboard if no role found
            logger.warning(f"No role found for user {user.email}, redirecting to default dashboard")
            return redirect(default_dashboard)
            
        except Exception as e:
            logger.error(f"Error in redirect_based_on_role: {str(e)}")
            messages.error(self.request, "An error occurred during login redirection.")
            return redirect('login')

def user_logout(request):
    if request.user.is_authenticated:
        logger.info(f"User logged out: {request.user.email} (Role: {request.user.role}).")
        logout(request)
        messages.success(request, 'You have been logged out.')
    return redirect('login')


class UserManagementView(View):
    def get_template_name(self):
        return get_template_path('users_dashboard.html', self.request.user.role, 'user_management')

    def get(self, request):
        try:
            users = CustomUser.objects.select_related('role').all()  # Add select_related to optimize queries
            
            # Update role-based queries
            patient_role = Role.objects.get(name='PATIENT')
            doctor_role = Role.objects.get(name='DOCTOR')
            
            # Get all roles for the filter dropdown
            roles = Role.objects.all()
            
            total_users = users.filter(is_active=True).count()
            doctor_count = users.filter(role=doctor_role, is_active=True).count()
            available_doctors = doctor_count
            new_users = users.filter(date_joined__gte=timezone.now().replace(day=1)).count()
            new_patients = users.filter(
                role=patient_role, 
                date_joined__gte=timezone.now().replace(day=1)
            ).count()

            # Pagination for users
            paginator = Paginator(users, 10)  # Show 10 users per page
            page = request.GET.get('page')
            try:
                users = paginator.page(page)
            except PageNotAnInteger:
                users = paginator.page(1)
            except EmptyPage:
                users = paginator.page(paginator.num_pages)

            # Context data to be passed to the template
            context = {
                'users': users,
                'roles': roles,  # Add roles to context
                'total_users': total_users,
                'doctor_count': doctor_count,
                'available_doctors': available_doctors,
                'new_users': new_users,
                'new_patients': new_patients,
                'paginator': paginator,
                'page_obj': users,
                'user_role': request.user.role,
            }

            return render(request, self.get_template_name(), context)

        except Exception as e:
            logger.error(f"Error in UserManagementView: {str(e)}")
            return HttpResponse(f"An error occurred: {str(e)}", status=500)
        
class UserProfileView(View):
    def get_template_name(self):
        return get_template_path('profile_management.html', self.request.user.role, 'profile')

    def get(self, request):
        try:
            context = {
                'user_role': request.user.role,
            }

            patient_role = Role.objects.get(name='PATIENT')
            doctor_role = Role.objects.get(name='DOCTOR')

            if request.user.role == patient_role:
                try:
                    # Try to fetch patient profile if it exists
                    patient_profile = Patient.objects.get(user=request.user)
                    medical_history = MedicalHistory.objects.filter(patient=patient_profile).first()
                    
                    context.update({
                        'patient_profile': patient_profile,
                        'medical_history': medical_history,
                        'has_patient_profile': True,
                        'blood_group_choices': Patient.BLOOD_GROUP_CHOICES,
                        'gender_choices': Patient.GENDER_CHOICES
                    })
                except Patient.DoesNotExist:
                    # If profile doesn't exist, provide necessary data for profile creation
                    context.update({
                        'has_patient_profile': False,
                        'blood_group_choices': Patient.BLOOD_GROUP_CHOICES,
                        'gender_choices': Patient.GENDER_CHOICES,
                        'error_message': 'Your patient profile has not been created yet. Please fill in the required information below.'
                    })

            elif request.user.role == doctor_role:
                # Existing doctor profile logic
                try:
                    doctor_profile = DoctorProfile.objects.get(user=request.user)
                    context.update({
                        'doctor_profile': doctor_profile,
                        'specializations': Specialization.objects.filter(is_active=True),
                        'treatment_methods': TreatmentMethodSpecialization.objects.filter(is_active=True),
                        'body_areas': BodyAreaSpecialization.objects.filter(is_active=True),
                        'associated_conditions': AssociatedConditionSpecialization.objects.filter(is_active=True),
                        'has_doctor_profile': True
                    })
                except DoctorProfile.DoesNotExist:
                    context.update({
                        'has_doctor_profile': False,
                        'specializations': Specialization.objects.filter(is_active=True),
                        'treatment_methods': TreatmentMethodSpecialization.objects.filter(is_active=True),
                        'body_areas': BodyAreaSpecialization.objects.filter(is_active=True),
                        'associated_conditions': AssociatedConditionSpecialization.objects.filter(is_active=True),
                    })

            return render(request, self.get_template_name(), context)

        except Exception as e:
            logger.error(f"Error in UserProfileView: {str(e)}")
            messages.error(request, "An error occurred while loading your profile.")
            return HttpResponse(f"An error occurred: {str(e)}", status=500)

    def post(self, request):
        try:
            if request.user.role == 'PATIENT':
                # Handle patient profile creation/update
                if not hasattr(request.user, 'patient_profile'):
                    patient_data = {
                        'user': request.user,
                        'date_of_birth': request.POST.get('date_of_birth'),
                        'gender': request.POST.get('gender'),
                        'blood_group': request.POST.get('blood_group'),
                        'address': request.POST.get('address'),
                        'phone_number': request.POST.get('phone_number'),
                        'emergency_contact_name': request.POST.get('emergency_contact_name'),
                        'emergency_contact_number': request.POST.get('emergency_contact_number'),
                        'vitiligo_onset_date': request.POST.get('vitiligo_onset_date'),
                        'vitiligo_type': request.POST.get('vitiligo_type'),
                        'affected_body_areas': request.POST.get('affected_body_areas'),
                    }
                    
                    patient = Patient.objects.create(**patient_data)
                    
                    # Create medical history
                    medical_history_data = {
                        'patient': patient,
                        'allergies': request.POST.get('allergies', ''),
                        'chronic_conditions': request.POST.get('chronic_conditions', ''),
                        'past_surgeries': request.POST.get('past_surgeries', ''),
                        'family_history': request.POST.get('family_history', ''),
                    }
                    
                    MedicalHistory.objects.create(**medical_history_data)
                    messages.success(request, "Patient profile created successfully!")
                else:
                    # Handle profile update logic here
                    patient = request.user.patient_profile
                    # Update fields based on POST data
                    # Similar to creation but with .update() instead
                    messages.success(request, "Patient profile updated successfully!")

                return redirect('patient_dashboard')

            # Handle other role profile updates here
            return redirect('dashboard')

        except Exception as e:
            logger.error(f"Error in UserProfileView POST: {str(e)}")
            messages.error(request, "An error occurred while saving your profile.")
            return redirect('profile_management')

class CreateUserView(View):
    def get_template_name(self):
        return get_template_path('create_user.html', self.request.user.role, 'user_management')

    def get(self, request):
        try:
            form = UserCreationForm()
            context = {
                'form': form,
                'user_role': request.user.role,
            }
            return render(request, self.get_template_name(), context)
        except Exception as e:
            logger.error(f"Error in CreateUserView GET: {str(e)}")
            messages.error(request, "An error occurred while loading the form.")
            return redirect('user_management')

    def post(self, request):
        try:
            form = UserCreationForm(request.POST, request.FILES)
            if form.is_valid():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()
                messages.success(request, f"User {user.email} created successfully.")
                return redirect('user_management')
            else:
                messages.error(request, "Please correct the errors below.")
                return render(request, self.get_template_name(), {'form': form})

        except Exception as e:
            logger.error(f"Error in CreateUserView POST: {str(e)}")
            messages.error(request, "An error occurred while creating the user.")
            return redirect('create_user')
