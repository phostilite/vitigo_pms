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
    path('export/<int:appointment_id>/', views.AppointmentExportSingleView.as_view(), name='appointment_export_single'),
    path('reminders/', views.AppointmentReminderView.as_view(), name='appointment_reminders'),
    path('reminders/create-template/', views.CreateReminderTemplateView.as_view(), name='create_reminder_template'),
    path('reminders/configure/', views.ConfigureReminderSettingsView.as_view(), name='configure_reminder_settings'),
    path('reminders/delete-template/<int:template_id>/', views.DeleteReminderTemplateView.as_view(), name='delete_reminder_template'),
    path('reminders/delete-config/<int:config_id>/', views.DeleteReminderConfigurationView.as_view(), name='delete_reminder_config'),
    path('reminders/edit-template/<int:template_id>/', views.EditReminderTemplateView.as_view(), name='edit_reminder_template'),
    path('reminders/edit-config/<int:config_id>/', views.EditReminderConfigurationView.as_view(), name='edit_reminder_config'),
    path('<int:appointment_id>/reschedule/', views.AppointmentRescheduleView.as_view(), name='appointment_reschedule'),
]