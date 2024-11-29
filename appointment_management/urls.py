# appointments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.AppointmentDashboardView.as_view(), name='appointment_dashboard'),
    path('<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment_detail'),
    path('create/', views.AppointmentCreateView.as_view(), name='appointment_create'),
]