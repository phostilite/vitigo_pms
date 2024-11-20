# views.py

import logging
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, FileResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import BodyPart, PatientImage, ImageComparison, ImageAnnotation
from .forms import PatientImageUploadForm
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.files.storage import default_storage
from django.template.defaultfilters import filesizeformat  # Add this import
import os
import json
import mimetypes

logger = logging.getLogger(__name__)

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

            # Add file size information
            for image in patient_images:
                if default_storage.exists(image.image_file.name):
                    image.file_size_formatted = filesizeformat(default_storage.size(image.image_file.name))
                else:
                    image.file_size_formatted = 'N/A'

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

class ImageUploadView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = PatientImage
    form_class = PatientImageUploadForm
    template_name = 'dashboard/admin/image_management/image_upload.html'
    success_url = reverse_lazy('image_management')

    def test_func(self):
        return self.request.user.role in ['ADMIN', 'DOCTOR', 'NURSE']

    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to upload images.")
        return redirect('image_management')

    def form_valid(self, form):
        try:
            instance = form.save(commit=False)
            instance.uploaded_by = self.request.user
            instance.save()
            
            logger.info(
                f"Image uploaded successfully - Patient: {instance.patient.id}, "
                f"Uploaded by: {self.request.user.id}, "
                f"File size: {instance.file_size} bytes"
            )
            
            # Store the image instance in the session for confirmation page
            self.request.session['uploaded_image_id'] = instance.id
            return redirect('image_upload_confirmation')
            
        except Exception as e:
            logger.error(f"Image upload failed - Error: {str(e)}", exc_info=True)
            messages.error(self.request, f'Failed to upload image: {str(e)}')
            return super().form_invalid(form)

    def form_invalid(self, form):
        logger.warning(
            f"Invalid image upload attempt - Errors: {form.errors}, "
            f"User: {self.request.user.id}"
        )
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class ImageUploadConfirmationView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role in ['ADMIN', 'DOCTOR', 'NURSE']

    def get(self, request):
        image_id = request.session.get('uploaded_image_id')
        if not image_id:
            return redirect('image_management')

        try:
            image = PatientImage.objects.get(id=image_id)
            # Clear the session
            del request.session['uploaded_image_id']
            
            return render(request, 'dashboard/admin/image_management/image_upload_confirmation.html', {
                'image': image
            })
        except PatientImage.DoesNotExist:
            return redirect('image_management')

class GetAnnotationsView(LoginRequiredMixin, View):
    def get(self, request, image_id):
        try:
            annotations = ImageAnnotation.objects.filter(image_id=image_id).select_related('created_by')
            data = [{
                'id': ann.id,
                'x': ann.x_coordinate,
                'y': ann.y_coordinate,
                'width': ann.width,
                'height': ann.height,
                'text': ann.text,
                'created_by': ann.created_by.get_full_name(),
                'created_at': ann.created_at.strftime('%Y-%m-%d %H:%M')
            } for ann in annotations]
            return JsonResponse({'annotations': data})
        except Exception as e:
            logger.error(f"Failed to fetch annotations: {str(e)}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class DownloadImageView(LoginRequiredMixin, View):
    def get(self, request, image_id):
        try:
            image = PatientImage.objects.get(id=image_id)
            
            # Check if user has permission to download the image
            if not request.user.is_staff and image.patient.user != request.user:
                return HttpResponseForbidden("You don't have permission to download this image")

            # Get the file path
            file_path = image.image_file.path
            
            # Get the original filename
            filename = os.path.basename(image.image_file.name)
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            
            # Open the file in binary mode
            response = FileResponse(open(file_path, 'rb'), content_type=content_type)
            
            # Set content disposition as attachment with original filename
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except PatientImage.DoesNotExist:
            messages.error(request, "Image not found")
            return redirect('image_management')
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}", exc_info=True)
            messages.error(request, "Error downloading image")
            return redirect('image_management')

class DeleteImageView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'ADMIN'

    def post(self, request, image_id):
        try:
            image = PatientImage.objects.get(id=image_id)
            
            # Store image details for logging
            image_details = {
                'patient': image.patient.user.get_full_name(),
                'file_name': image.image_file.name,
                'uploaded_by': image.uploaded_by.get_full_name() if image.uploaded_by else 'Unknown'
            }
            
            # Delete the image file from storage
            if default_storage.exists(image.image_file.name):
                default_storage.delete(image.image_file.name)
            
            # Delete the database record
            image.delete()
            
            logger.info(
                f"Image deleted successfully - Patient: {image_details['patient']}, "
                f"File: {image_details['file_name']}, "
                f"Deleted by: {request.user.get_full_name()}"
            )
            
            messages.success(request, "Image deleted successfully")
            return redirect('image_management')
            
        except PatientImage.DoesNotExist:
            messages.error(request, "Image not found")
            return redirect('image_management')
        except Exception as e:
            logger.error(f"Error deleting image: {str(e)}", exc_info=True)
            messages.error(request, f"Error deleting image: {str(e)}")
            return redirect('image_management')

class ImageDetailView(LoginRequiredMixin, View):
    def get(self, request, image_id):
        try:
            image = PatientImage.objects.select_related(
                'patient', 'patient__user', 'body_part', 'uploaded_by'
            ).get(id=image_id)
            
            # Get all images of the same patient
            related_images = PatientImage.objects.filter(
                patient=image.patient
            ).exclude(id=image_id).order_by('-date_taken')[:5]
            
            # Get comparisons containing this image
            comparisons = ImageComparison.objects.filter(
                images=image
            ).select_related('created_by')
            
            # Get annotations for this image
            annotations = image.annotations.select_related('created_by').order_by('-created_at')
            
            # Get images from same body part
            similar_images = PatientImage.objects.filter(
                body_part=image.body_part
            ).exclude(id=image_id).order_by('-date_taken')[:5]
            
            context = {
                'image': image,
                'related_images': related_images,
                'comparisons': comparisons,
                'annotations': annotations,
                'similar_images': similar_images,
            }
            
            return render(request, 'dashboard/admin/image_management/image_detail.html', context)
            
        except PatientImage.DoesNotExist:
            messages.error(request, "Image not found")
            return redirect('image_management')

