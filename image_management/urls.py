from django.urls import path
from .views import (ImageManagementView, ImageUploadView, ImageUploadConfirmationView, 
                   GetAnnotationsView)

urlpatterns = [
    path('', ImageManagementView.as_view(), name='image_management'),
    path('upload/', ImageUploadView.as_view(), name='image_upload'),
    path('upload/confirmation/', ImageUploadConfirmationView.as_view(), name='image_upload_confirmation'),
    path('image/<int:image_id>/annotations/', GetAnnotationsView.as_view(), name='get_annotations'),
]