# appointments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.AppointmentDashboardView.as_view(), name='appointment_dashboard'),
    path('<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment_detail'),
    path('create/', views.AppointmentCreateView.as_view(), name='appointment_create'),
    path('get-time-slots/', views.get_available_time_slots, name='get_available_time_slots'),
    path('user/<int:user_id>/', views.get_user_info, name='get_user_info'),
]