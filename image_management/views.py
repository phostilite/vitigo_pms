# Python Standard Library imports
import json
import logging
import mimetypes
import os
import csv
from io import StringIO

# Django core imports
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.files.storage import default_storage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Count, Q
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, FileResponse
from django.shortcuts import render, redirect
from django.template.defaultfilters import filesizeformat
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic.edit import CreateView

# Local application imports
from access_control.models import Role
from access_control.permissions import PermissionManager
from error_handling.views import handler403
from .forms import PatientImageUploadForm
from .models import BodyPart, PatientImage, ImageComparison, ImageAnnotation

# Logger configuration
logger = logging.getLogger(__name__)

def get_template_path(base_template, role, module='image_management'):
    """
    Simple template path resolver based on user role
    """
    if isinstance(role, Role):
        role_folder = role.template_folder
    else:
        role = Role.objects.get(name=role)
        role_folder = role.template_folder
    
    return f'dashboard/{role_folder}/{module}/{base_template}'

class ImageManagementView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            # Check module access permission
            if not PermissionManager.check_module_access(request.user, 'image_management'):
                messages.error(request, "You don't have permission to access Image Management")
                return handler403(request, exception="Access Denied")

            # Get template path
            template_path = get_template_path('image_dashboard.html', request.user.role)
            logger.info(f"Template path resolved to: {template_path}")
            
            # Get filter parameters
            image_type = request.GET.get('image_type', '')
            body_part = request.GET.get('body_part', '')
            date_from = request.GET.get('date_from', '')
            date_to = request.GET.get('date_to', '')
            search_query = request.GET.get('search', '')

            # Get all body parts for filter dropdown
            body_parts = BodyPart.objects.all().order_by('name')

            # Base queryset
            patient_images = PatientImage.objects.select_related(
                'patient', 'patient__user', 'body_part'
            ).order_by('-date_taken')

            # Apply filters
            if image_type:
                patient_images = patient_images.filter(image_type=image_type)
            if body_part:
                patient_images = patient_images.filter(body_part_id=body_part)
            if date_from:
                patient_images = patient_images.filter(date_taken__gte=date_from)
            if date_to:
                patient_images = patient_images.filter(date_taken__lte=date_to)
            if search_query:
                patient_images = patient_images.filter(
                    Q(patient__user__first_name__icontains=search_query) |
                    Q(patient__user__last_name__icontains=search_query) |
                    Q(body_part__name__icontains=search_query) |
                    Q(notes__icontains=search_query)
                )

            # Calculate statistics
            total_images = patient_images.count()
            recent_uploads = patient_images.filter(
                uploaded_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).count()
            total_comparisons = ImageComparison.objects.count()
            storage_used = patient_images.aggregate(total_size=Sum('file_size'))['total_size'] or 0
            storage_used = round(storage_used / (1024 * 1024 * 1024), 2)  # Convert to GB

            # Setup pagination
            paginator = Paginator(patient_images, 12)
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
                    image.file_size_formatted = filesizeformat(
                        default_storage.size(image.image_file.name)
                    )
                else:
                    image.file_size_formatted = 'N/A'

            context = {
                'body_parts': body_parts,
                'patient_images': patient_images,
                'total_images': total_images,
                'recent_uploads': recent_uploads,
                'total_comparisons': total_comparisons,
                'storage_used': storage_used,
                'paginator': paginator,
                'page_obj': patient_images,
                'current_filters': {
                    'image_type': image_type,
                    'body_part': body_part,
                    'date_from': date_from,
                    'date_to': date_to,
                    'search': search_query,
                }
            }

            return render(request, template_path, context)

        except Exception as e:
            logger.error(f"Error in ImageManagementView: {str(e)}", exc_info=True)
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('dashboard')

class ImageUploadView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = PatientImage
    form_class = PatientImageUploadForm
    template_name = None  # Remove default template_name
    success_url = reverse_lazy('image_management')

    def get_template_name(self):
        # Get correct template path based on user's role
        return get_template_path('image_upload.html', self.request.user.role, 'image_management')

    def test_func(self):
        # Replace get_permissions() with check_module_modify()
        return PermissionManager.check_module_modify(self.request.user, 'image_management')

    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, "You don't have permission to upload images")
            return handler403(request, exception="Insufficient Permissions")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Override get method to use correct template
        self.template_name = self.get_template_name()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Override post method to use correct template
        self.template_name = self.get_template_name()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            instance = form.save(commit=False)
            instance.uploaded_by = self.request.user
            instance.save()
            form.save_m2m()  # Save many-to-many relationships if any
            
            logger.info(
                f"Image uploaded successfully - Patient: {instance.patient.id}, "
                f"Uploaded by: {self.request.user.id}, "
                f"File size: {instance.file_size} bytes"
            )
            
            messages.success(self.request, 'Image uploaded successfully.')
            return redirect('image_management')
            
        except Exception as e:
            logger.error(f"Image upload failed - Error: {str(e)}", exc_info=True)
            messages.error(self.request, f'Failed to upload image: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.warning(
            f"Invalid image upload attempt - Errors: {form.errors}, "
            f"User: {self.request.user.id}"
        )
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['template_name'] = self.get_template_name()
        return context

class ImageUploadConfirmationView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # Replace role string check with proper permission check
        return PermissionManager.check_module_modify(self.request.user, 'image_management')

    def get(self, request):
        image_id = request.session.get('uploaded_image_id')
        if not image_id:
            return redirect('image_management')

        try:
            image = PatientImage.objects.get(id=image_id)
            # Clear the session
            del request.session['uploaded_image_id']
            
            template_path = get_template_path('image_upload_confirmation.html', request.user.role, 'image_management')
            return render(request, template_path, {'image': image})
        except PatientImage.DoesNotExist:
            return redirect('image_management')

class GetAnnotationsView(LoginRequiredMixin, View):
    def get(self, request, image_id):
        # Add permission check
        if not PermissionManager.check_module_access(request.user, 'image_management'):
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

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
        # Add permission check
        if not PermissionManager.check_module_access(request.user, 'image_management'):
            return HttpResponseForbidden("You don't have permission to access images")

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
        # Replace get_permissions() with check_module_delete()
        return PermissionManager.check_module_delete(self.request.user, 'image_management')

    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, "You don't have permission to delete images")
            return handler403(request, exception="Insufficient Permissions")
        return super().dispatch(request, *args, **kwargs)

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
            # Replace get_permissions() with check_module_access()
            if not PermissionManager.check_module_access(request.user, 'image_management'):
                messages.error(request, "You don't have permission to view image details")
                return handler403(request, exception="Access Denied")

            template_path = get_template_path('image_detail.html', request.user.role)
            # No need to check template_path existence since get_template_path was simplified

            image = PatientImage.objects.select_related(
                'patient', 'patient__user', 'body_part', 'uploaded_by'
            ).get(id=image_id)
            
            # Get all images of the same patient
            related_images = PatientImage.objects.filter(
                patient=image.patient
            ).exclude(id=image_id).order_by('-date_taken')
            
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
            
            return render(request, template_path, context)
            
        except PatientImage.DoesNotExist:
            messages.error(request, "Image not found")
            return redirect('image_management')

class ImageComparisonView(LoginRequiredMixin, View):
    def get(self, request):
        if not PermissionManager.check_module_access(request.user, 'image_management'):
            messages.error(request, "You don't have permission to access Image Comparison")
            return handler403(request, exception="Access Denied")

        template_path = get_template_path('image_comparison_select.html', request.user.role)
        
        try:
            # Get all available images for selection
            available_images = PatientImage.objects.select_related(
                'patient', 'patient__user', 'body_part'
            ).order_by('-date_taken')
            
            context = {
                'available_images': available_images,
            }
            
            return render(request, template_path, context)
            
        except Exception as e:
            logger.error(f"Error in image comparison view: {str(e)}", exc_info=True)
            messages.error(request, f"An error occurred while loading images: {str(e)}")
            return redirect('image_management')

class ImageComparisonResultView(LoginRequiredMixin, View):
    def get(self, request):
        if not PermissionManager.check_module_access(request.user, 'image_management'):
            messages.error(request, "You don't have permission to access Image Comparison")
            return handler403(request, exception="Access Denied")

        try:
            selected_ids = request.GET.getlist('images', [])
            if not selected_ids:
                messages.warning(request, "Please select images to compare")
                return redirect('image_comparison')

            selected_images = PatientImage.objects.select_related(
                'patient', 'patient__user', 'body_part'
            ).filter(id__in=selected_ids)

            if not selected_images.exists():
                messages.error(request, "No valid images selected")
                return redirect('image_comparison')

            # Add file size formatted for each image
            for image in selected_images:
                if default_storage.exists(image.image_file.name):
                    image.file_size_formatted = filesizeformat(
                        default_storage.size(image.image_file.name)
                    )
                else:
                    image.file_size_formatted = 'N/A'

            template_path = get_template_path('image_comparison_result.html', request.user.role)
            context = {
                'selected_images': selected_images,
                'comparison_date': timezone.now(),
            }
            
            return render(request, template_path, context)

        except Exception as e:
            logger.error(f"Error in image comparison result view: {str(e)}", exc_info=True)
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('image_comparison')

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class ImageExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'image_management')

    def get(self, request):
        try:
            export_format = request.GET.get('format', 'csv')
            date_from = request.GET.get('date_from')
            date_to = request.GET.get('date_to')

            # Get filtered queryset
            queryset = PatientImage.objects.select_related(
                'patient', 'patient__user', 'body_part', 'uploaded_by'
            ).order_by('-date_taken')

            if date_from:
                queryset = queryset.filter(date_taken__gte=date_from)
            if date_to:
                queryset = queryset.filter(date_taken__lte=date_to)

            if export_format == 'csv':
                return self.export_csv(queryset)
            elif export_format == 'pdf':
                return self.export_pdf(queryset)
            else:
                messages.error(request, "Invalid export format")
                return redirect('image_management')

        except Exception as e:
            logger.error(f"Export failed: {str(e)}", exc_info=True)
            messages.error(request, f"Export failed: {str(e)}")
            return redirect('image_management')

    def export_csv(self, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="image_report_{timezone.now().strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Image ID', 'Patient Name', 'Body Part', 'Type', 'Date Taken',
            'Upload Date', 'Uploaded By', 'Private', 'Size (bytes)',
            'Dimensions', 'Tags', 'Notes'
        ])

        for image in queryset:
            writer.writerow([
                image.id,
                image.patient.user.get_full_name(),
                image.body_part.name if image.body_part else 'N/A',
                image.get_image_type_display(),
                image.date_taken.strftime('%Y-%m-%d'),
                image.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
                image.uploaded_by.get_full_name() if image.uploaded_by else 'N/A',
                'Yes' if image.is_private else 'No',
                image.file_size or 'N/A',
                f'{image.width}x{image.height}' if image.width and image.height else 'N/A',
                ', '.join(tag.name for tag in image.tags.all()),
                image.notes[:100] + '...' if len(image.notes) > 100 else image.notes
            ])

        return response

    def export_pdf(self, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="image_report_{timezone.now().strftime("%Y%m%d")}.pdf"'

        doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )

        # Title
        elements.append(Paragraph('Image Management Report', title_style))
        elements.append(Spacer(1, 20))

        # Summary statistics
        total_images = queryset.count()
        total_size = sum(image.file_size or 0 for image in queryset)
        private_count = queryset.filter(is_private=True).count()

        stats = [
            ['Total Images:', str(total_images)],
            ['Total Storage:', f'{total_size / (1024*1024):.2f} MB'],
            ['Private Images:', str(private_count)],
            ['Date Range:', f"{queryset.last().date_taken if queryset.exists() else 'N/A'} to {queryset.first().date_taken if queryset.exists() else 'N/A'}"]
        ]

        stats_table = Table(stats, colWidths=[100, 150])
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 20))

        # Image list
        data = [['Patient', 'Body Part', 'Type', 'Date Taken', 'Size', 'Private']]
        for image in queryset:
            data.append([
                image.patient.user.get_full_name(),
                image.body_part.name if image.body_part else 'N/A',
                image.get_image_type_display(),
                image.date_taken.strftime('%Y-%m-%d'),
                f'{image.file_size/1024:.1f} KB' if image.file_size else 'N/A',
                'Yes' if image.is_private else 'No'
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)

        doc.build(elements)
        return response

