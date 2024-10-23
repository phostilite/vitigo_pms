from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.UserRegistrationAPIView.as_view(), name='api_register'),
    path('login/', views.UserLoginAPIView.as_view(), name='api_login'),
    
    path('user-info/', views.UserInfoView.as_view(), name='user_info'),
    path('basic-user-info/update/', views.BasicUserInfoUpdateAPIView.as_view(), name='user-update'),
    
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('reset-password/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    path('patient-info/', views.PatientInfoView.as_view(), name='patient-info'),

    path('doctors/', views.DoctorListView.as_view(), name='doctor-list'),
    path('doctors/<int:doctor_id>/', views.DoctorDetailView.as_view(), name='doctor-detail'),
    
    path('appointments/', views.UserAppointmentsView.as_view(), name='user-appointments-list'),
    path('appointments/<int:appointment_id>/', views.UserAppointmentDetailView.as_view(), name='user-appointment-detail'),
    path('appointments/available-time-slots/', views.AvailableTimeSlotsView.as_view(), name='available-time-slots'),
    path('appointments/types/', views.AppointmentTypesView.as_view(), name='appointment-types'),
    path('appointments/statuses/', views.AppointmentStatusView.as_view(), name='appointment-statuses'),
    path('appointments/priorities/', views.AppointmentPriorityView.as_view(), name='appointment-priorities'),
    path('appointments/create/', views.CreateAppointmentView.as_view(), name='create-appointment'),

    path('queries/', views.UserQueriesView.as_view(), name='user-queries'),
]