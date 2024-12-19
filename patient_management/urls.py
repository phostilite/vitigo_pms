from django.urls import path
from . import views

urlpatterns = [
    path('', views.PatientListView.as_view(), name='patient_list'),
    path('<int:user_id>/detail/', views.PatientDetailView.as_view(), name='patient_detail'),
    path('register/', views.PatientRegistrationView.as_view(), name='patient_registration'),
]