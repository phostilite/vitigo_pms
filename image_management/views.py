# views.py

from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from .models import BodyPart, PatientImage, ImageComparison
from django.db.models import Sum, Count
from django.utils import timezone

class ImageManagementView(View):
    template_name = 'dashboard/admin/image_management/image_dashboard.html'

    def get(self, request):
        try:
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

            return render(request, self.template_name, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)