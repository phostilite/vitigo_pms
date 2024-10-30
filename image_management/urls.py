from django.urls import path
from . import views

urlpatterns = [
    path('', views.ImageManagementView.as_view(), name='image_management'),
]