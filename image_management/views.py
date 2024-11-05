# views.py

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from .models import BodyPart, PatientImage, ImageComparison
from django.db.models import Sum, Count
from django.utils import timezone

def get_template_path(base_template, user_role):
    """
    Resolves template path based on user role.
    Example: For 'image_dashboard.html' and role 'ACCOUNTANT', 
    returns 'dashboard/accountant/image_management/image_dashboard.html'
    """
    # Only roles that should have access to image management
    role_template_map = {
        'ADMIN': 'admin',
        'DOCTOR': 'doctor',
        'NURSE': 'nurse',
        'LAB_TECHNICIAN': 'lab',
        'TECHNICIAN': 'technician'
    }
    
    role_folder = role_template_map.get(user_role)
    if not role_folder:
        return None
    return f'dashboard/{role_folder}/image_management/{base_template}'

class ImageManagementView(View):
    def get(self, request):
        try:
            # Get user role from request
            user_role = request.user.role if hasattr(request.user, 'role') else None
            
            # Resolve template path
            template_path = get_template_path('image_dashboard.html', user_role)
            if not template_path:
                return HttpResponseForbidden("You don't have permission to access this page")

            # Fetch all body parts and patient images
            body_parts = BodyPart.objects.all()
            patient_images = PatientImage.objects.all()

            # Calculate statistics
            total_images = patient_images.count()
            recent_uploads = patient_images.filter(uploaded_at__gte=timezone.now() - timezone.timedelta(days=7)).count()
            total_comparisons = ImageComparison.objects.count()
            storage_used = patient_images.aggregate(total_size=Sum('file_size'))['total_size'] or 0
            storage_used = round(storage_used / (1024 * 1024 * 1024), 2)  # Convert bytes to GB

            # Pagination for patient images
            paginator = Paginator(patient_images, 12)  # Show 12 images per page
            page = request.GET.get('page')
            try:
                patient_images = paginator.page(page)
            except PageNotAnInteger:
                patient_images = paginator.page(1)
            except EmptyPage:
                patient_images = paginator.page(paginator.num_pages)

            # Context data to be passed to the template
            context = {
                'body_parts': body_parts,
                'patient_images': patient_images,
                'total_images': total_images,
                'recent_uploads': recent_uploads,
                'total_comparisons': total_comparisons,
                'storage_used': storage_used,
                'paginator': paginator,
                'page_obj': patient_images,
            }

            return render(request, template_path, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)