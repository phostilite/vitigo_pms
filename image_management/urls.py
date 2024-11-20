from django.urls import path
from .views import (ImageManagementView, ImageUploadView, ImageUploadConfirmationView, 
                   GetAnnotationsView, DownloadImageView, DeleteImageView)

urlpatterns = [
    path('', ImageManagementView.as_view(), name='image_management'),
    path('upload/', ImageUploadView.as_view(), name='image_upload'),
    path('upload/confirmation/', ImageUploadConfirmationView.as_view(), name='image_upload_confirmation'),
    path('image/<int:image_id>/annotations/', GetAnnotationsView.as_view(), name='get_annotations'),
    path('image/<int:image_id>/download/', DownloadImageView.as_view(), name='download_image'),
    path('image/<int:image_id>/delete/', DeleteImageView.as_view(), name='delete_image'),
]