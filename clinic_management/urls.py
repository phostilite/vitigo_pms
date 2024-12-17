# URLs configuration (add to urls.py)
from django.urls import path
from . import views

app_name = 'clinic_management'

urlpatterns = [
    path('', views.ClinicManagementView.as_view(), name='clinic_dashboard'),
]
