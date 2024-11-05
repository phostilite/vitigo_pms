from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from .forms import UserRegistrationForm, UserLoginForm
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from user_management.models import CustomUser
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from doctor_management.models import DoctorProfile, Specialization, TreatmentMethodSpecialization, BodyAreaSpecialization, AssociatedConditionSpecialization
from patient_management.models import Patient, MedicalHistory

logger = logging.getLogger(__name__)

def get_template_path(base_template, user_role, module=''):
    """
    Resolves template path based on user role.
    Example: For 'users_dashboard.html', 'DOCTOR', and module='user_management' 
    returns 'dashboard/doctor/user_management/users_dashboard.html'
    """
    role_template_map = {
        'ADMIN': 'admin',
        'DOCTOR': 'doctor',
        'NURSE': 'nurse',
        'RECEPTIONIST': 'receptionist',
        'PHARMACIST': 'pharmacist',
        'LAB_TECHNICIAN': 'lab',
        'PATIENT': 'patient'
    }
    
    role_folder = role_template_map.get(user_role, 'admin')
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
        role_redirect_map = {
            'ADMIN': 'admin_dashboard',
            'DOCTOR': 'doctor_dashboard',
            'PATIENT': 'patient_dashboard',
            # Add other roles as needed
        }
        return redirect(role_redirect_map.get(user.role, 'dashboard'))

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
            # Fetch all users
            users = CustomUser.objects.all()

            # Calculate statistics
            total_users = users.filter(is_active=True).count()
            doctor_count = users.filter(role='DOCTOR', is_active=True).count()
            available_doctors = doctor_count  # Assuming all active doctors are available today
            new_users = users.filter(date_joined__gte=timezone.now().replace(day=1)).count()
            new_patients = users.filter(role='PATIENT', date_joined__gte=timezone.now().replace(day=1)).count()

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

            if request.user.role == 'PATIENT':
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

            elif request.user.role == 'DOCTOR':
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