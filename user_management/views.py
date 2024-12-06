# Standard library imports
import logging
import random
import string

# Django core imports
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

# Local application imports
from access_control.models import Role
from access_control.permissions import PermissionManager
from appointment_management.models import Appointment
from consultation_management.models import Consultation
from doctor_management.models import (
    DoctorProfile,
    Specialization,
    TreatmentMethodSpecialization,
    BodyAreaSpecialization,
    AssociatedConditionSpecialization
)
from error_handling.views import handler400, handler403, handler404, handler500
from patient_management.models import Patient, MedicalHistory
from .forms import (
    UserRegistrationForm,
    UserLoginForm,
    UserCreationForm,
    UserEditForm
)

# Configure logging and user model
User = get_user_model()
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
        try:
            form = UserRegistrationForm(request.POST)
            if form.is_valid():
                user = form.save()
                login(request, user)
                logger.info(f"New patient registered: {user.email}.")
                messages.success(request, 'Registration successful.')
                return redirect('patient_dashboard')
            else:
                logger.warning(f"Registration failed. Errors: {form.errors}")
                return render(request, 'user_management/register.html', {'form': form})
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return handler500(request, exception=str(e))

class UserLoginView(View):
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        if request.user.is_authenticated:
            return self.redirect_based_on_role(request.user)
        form = UserLoginForm()
        return render(request, 'user_management/login.html', {'form': form})

    def post(self, request):
        try:
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
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return handler500(request, exception=str(e))

    def redirect_based_on_role(self, user):
        """
        Redirects user to appropriate dashboard based on their role
        """
        try:
            # Default fallback dashboard
            default_dashboard = 'dashboard'
            
            # Get role-based redirects
            role_redirects = {
                'SUPER_ADMIN': 'dashboard',
                'ADMIN': 'dashboard',
                'MANAGER': 'dashboard',
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


class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'user_management')
        
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_access(self.request.user, 'user_management'):
            messages.error(request, "You don't have permission to access user management")
            return handler403(request, exception="Insufficient Permissions")
        return super().dispatch(request, *args, **kwargs)

    def get_template_name(self):
        return get_template_path('users_dashboard.html', self.request.user.role, 'user_management')

    def get(self, request):
        try:
            users = User.objects.select_related('role').all()  # Add select_related to optimize queries
            
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
            return handler500(request, exception=str(e))
        
class UserProfileView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'user_management')
        
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_access(self.request.user, 'user_management'):
            messages.error(request, "You don't have permission to access profile management")
            return handler403(request, exception="Insufficient Permissions")
        return super().dispatch(request, *args, **kwargs)

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

        except PermissionDenied:
            return handler403(request, exception="Insufficient permissions to access profile")
        except Exception as e:
            logger.error(f"Profile view error: {str(e)}")
            messages.error(request, "An error occurred while loading your profile.")
            return handler500(request, exception=str(e))

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

class CreateUserView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_modify(self.request.user, 'user_management')
        
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_modify(self.request.user, 'user_management'):
            messages.error(request, "You don't have permission to create users")
            return handler403(request, exception="Insufficient Permissions")
        return super().dispatch(request, *args, **kwargs)

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
        except PermissionDenied:
            return handler403(request, exception="You don't have permission to create users")
        except Exception as e:
            logger.error(f"Error in CreateUserView GET: {str(e)}")
            return handler500(request, exception=str(e))

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
            return handler500(request, exception=str(e))

class UserDetailsView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'user_management')
        
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_access(self.request.user, 'user_management'):
            messages.error(request, "You don't have permission to view user details")
            return handler403(request, exception="Insufficient Permissions")
        return super().dispatch(request, *args, **kwargs)

    def get_template_name(self):
        return get_template_path('user_details.html', self.request.user.role, 'user_management')

    def get_doctor_patient_count(self, doctor_user):
        """Helper method to get total unique patients for a doctor"""
        try:
            # Get unique patient IDs from appointments (completed or confirmed)
            appointment_patient_ids = set(Appointment.objects.filter(
                doctor=doctor_user,
                status__in=['COMPLETED', 'CONFIRMED']
            ).values_list('patient_id', flat=True))

            # Get unique patient IDs from consultations
            consultation_patient_ids = set(Consultation.objects.filter(
                doctor=doctor_user
            ).values_list('patient_id', flat=True))

            # Combine both sets to get unique patients
            total_unique_patients = len(appointment_patient_ids.union(consultation_patient_ids))
            
            return total_unique_patients

        except Exception as e:
            logger.error(f"Error calculating doctor's patient count: {str(e)}")
            return 0

    def get(self, request, user_id):
        try:
            # Get the user being viewed with related role
            viewed_user = User.objects.select_related('role').get(id=user_id)
            
            # Base context
            context = {
                'user': viewed_user,
                'viewing_user': request.user,
                'user_role': request.user.role,
            }

            # Add role-specific data
            if viewed_user.role.name == 'DOCTOR':
                try:
                    doctor_profile = DoctorProfile.objects.get(user=viewed_user)
                    
                    # Get patient count using the new helper method
                    total_patients = self.get_doctor_patient_count(viewed_user)
                    
                    # Get recent appointments
                    recent_appointments = Appointment.objects.filter(
                        doctor=viewed_user,
                        status__in=['COMPLETED', 'CONFIRMED']
                    ).order_by('-date')[:5]
                    
                    # Get recent consultations
                    recent_consultations = Consultation.objects.filter(
                        doctor=viewed_user
                    ).order_by('-date_time')[:5]
                    
                    context.update({
                        'doctor_profile': doctor_profile,
                        'total_patients': total_patients,
                        'recent_appointments': recent_appointments,
                        'recent_consultations': recent_consultations,
                    })
                except DoctorProfile.DoesNotExist:
                    context.update({
                        'doctor_profile': None,
                        'total_patients': 0,
                    })

            elif viewed_user.role.name == 'PATIENT':
                try:
                    patient_profile = Patient.objects.get(user=viewed_user)
                    total_appointments = viewed_user.appointments.count() if hasattr(viewed_user, 'appointments') else 0
                    context.update({
                        'patient_profile': patient_profile,
                        'total_appointments': total_appointments,
                    })
                except Patient.DoesNotExist:
                    context.update({
                        'patient_profile': None,
                        'total_appointments': 0,
                    })

            return render(request, self.get_template_name(), context)

        except User.DoesNotExist:
            logger.warning(f"User with id {user_id} not found")
            return handler404(request, exception="User not found")
        except PermissionDenied:
            logger.warning(f"Permission denied for user {request.user.email} accessing user {user_id}")
            return handler403(request, exception="Access Denied")
        except Exception as e:
            logger.error(f"Error in UserDetailsView: {str(e)}")
            return handler500(request, exception=str(e))

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_delete(self.request.user, 'user_management')
        
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_delete(self.request.user, 'user_management'):
            messages.error(request, "You don't have permission to delete users")
            return handler403(request, exception="Insufficient Permissions")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, user_id):
        try:
            user = get_object_or_404(User, id=user_id)
            
            # Prevent self-deletion
            if user == request.user:
                messages.error(request, "You cannot delete your own account")
                return redirect('user_management')
                
            # Store user info for message
            user_email = user.email
            user_name = user.get_full_name()
            
            with transaction.atomic():
                # Delete associated profiles if they exist
                if hasattr(user, 'patient_profile'):
                    user.patient_profile.delete()
                if hasattr(user, 'doctor_profile'):
                    user.doctor_profile.delete()
                    
                user.delete()
            
            messages.success(request, f"User {user_name} ({user_email}) has been deleted successfully")
            logger.info(f"User {user_email} deleted by {request.user.email}")
            return redirect('user_management')
            
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            messages.error(request, f"Error deleting user: {str(e)}")
            return redirect('user_management')

class UserDeactivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_modify(self.request.user, 'user_management')
        
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_modify(self.request.user, 'user_management'):
            messages.error(request, "You don't have permission to deactivate users")
            return handler403(request, exception="Insufficient Permissions")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, user_id):
        try:
            user = get_object_or_404(User, id=user_id)
            
            # Prevent self-deactivation
            if user == request.user:
                messages.error(request, "You cannot deactivate your own account")
                return redirect('user_management')
            
            # Toggle user's active status
            new_status = not user.is_active
            user.is_active = new_status
            user.save()
            
            action = "activated" if new_status else "deactivated"
            messages.success(request, f"User {user.get_full_name()} has been {action} successfully")
            logger.info(f"User {user.email} {action} by {request.user.email}")
            
            return redirect('user_management')
            
        except Http404:
            return handler404(request, exception=f"User {user_id} not found")
        except PermissionDenied:
            return handler403(request, exception="Insufficient permissions to deactivate users")
        except Exception as e:
            logger.error(f"User deactivation error: {str(e)}")
            return handler500(request, exception=str(e))

class UserResetPasswordView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_modify(self.request.user, 'user_management')
        
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_modify(self.request.user, 'user_management'):
            messages.error(request, "You don't have permission to reset passwords")
            return handler403(request, exception="Insufficient Permissions")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, user_id):
        try:
            user = get_object_or_404(User, id=user_id)
            
            # Prevent self-password reset through this view
            if user == request.user:
                messages.error(request, "Use the profile settings to change your own password")
                return redirect('user_management')
            
            # Generate a random password
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            
            # Set the new password
            user.set_password(new_password)
            user.save()
            
            messages.success(
                request, 
                f"Password has been reset for {user.get_full_name()}. "
                f"New password: {new_password}"
            )
            logger.info(f"Password reset for user {user.email} by {request.user.email}")
            
            return redirect('user_management')
            
        except Http404:
            return handler404(request, exception=f"User {user_id} not found")
        except PermissionDenied:
            return handler403(request, exception="Insufficient permissions to reset passwords")
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            return handler500(request, exception=str(e))

class UserEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_modify(self.request.user, 'user_management')
        
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_modify(self.request.user, 'user_management'):
            messages.error(request, "You don't have permission to edit users")
            return handler403(request, exception="Insufficient Permissions")
        return super().dispatch(request, *args, **kwargs)

    def get_template_name(self):
        return get_template_path('edit_user.html', self.request.user.role, 'user_management')

    def get(self, request, user_id):
        try:
            user = get_object_or_404(User.objects.select_related('role'), id=user_id)
            form = UserEditForm(instance=user)
            
            context = {
                'form': form,
                'edited_user': user,
                'user_role': request.user.role,
            }
            
            return render(request, self.get_template_name(), context)
            
        except Http404:
            return handler404(request, exception=f"User {user_id} not found")
        except Exception as e:
            logger.error(f"Error in UserEditView GET: {str(e)}")
            return handler500(request, exception=str(e))

    def post(self, request, user_id):
        try:
            user = get_object_or_404(User, id=user_id)
            form = UserEditForm(request.POST, request.FILES, instance=user)
            
            if form.is_valid():
                # Prevent role change for self
                if user == request.user and 'role' in form.changed_data:
                    messages.error(request, "You cannot change your own role")
                    return render(request, self.get_template_name(), {'form': form, 'edited_user': user})
                
                # Save the form
                user = form.save()
                messages.success(request, f"User {user.get_full_name()} updated successfully")
                logger.info(f"User {user.email} updated by {request.user.email}")
                return redirect('user_detail', user_id=user.id)
            else:
                messages.error(request, "Please correct the errors below.")
                return render(request, self.get_template_name(), {'form': form, 'edited_user': user})
                
        except Http404:
            return handler404(request, exception=f"User {user_id} not found")
        except Exception as e:
            logger.error(f"Error in UserEditView POST: {str(e)}")
            return handler500(request, exception=str(e))