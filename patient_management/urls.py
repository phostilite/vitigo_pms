from django.urls import path
from . import views

urlpatterns = [
    path('', views.PatientListView.as_view(), name='patient_list'),
    path('<int:user_id>/detail/', views.PatientDetailView.as_view(), name='patient_detail'),
    path('register/', views.PatientRegistrationView.as_view(), name='patient_registration'),
    path('<int:user_id>/create-profile/', views.CreatePatientProfileView.as_view(), name='create_patient_profile'),
    path('<int:user_id>/edit-profile/', views.EditPatientProfileView.as_view(), name='edit_patient_profile'),
]