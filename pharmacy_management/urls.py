from django.urls import path
from . import views

urlpatterns = [
    path('', views.PharmacyManagementView.as_view(), name='pharmacy_management'),
]