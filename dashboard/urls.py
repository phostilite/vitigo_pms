from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_router, name='dashboard'),
    path('patient/', views.patient_dashboard, name='patient_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
]