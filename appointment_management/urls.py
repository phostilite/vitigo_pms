# appointments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.AppointmentDashboardView.as_view(), name='appointment_dashboard'),
    path('<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment_detail'),
    path('doctor-timeslots/', views.get_doctor_timeslots, name='doctor_timeslots'),
    path('create/', views.AppointmentCreateView.as_view(), name='appointment_create'),
    path('doctor-timeslots/<int:timeslot_id>/', views.update_doctor_timeslot, name='update_doctor_timeslot'),
    path('appointments/<int:appointment_id>/timeslot/', views.update_appointment_timeslot, name='update_appointment_timeslot'),
    path('<int:appointment_id>/status/', views.update_appointment_status, name='update_appointment_status'),
    path('<int:appointment_id>/delete/', views.AppointmentDeleteView.as_view(), name='appointment_delete'),
    path('export/', views.AppointmentExportView.as_view(), name='appointment_export'),
    path('reminders/', views.AppointmentReminderView.as_view(), name='appointment_reminders'),
]