from django.urls import path
from . import views

urlpatterns = [
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('nurse/', views.nurse_dashboard, name='nurse_dashboard'),
    path('medical/', views.medical_dashboard, name='medical_dashboard'),
    path('reception/', views.reception_dashboard, name='reception_dashboard'),
    path('pharmacy/', views.pharmacy_dashboard, name='pharmacy_dashboard'),
    path('lab/', views.lab_dashboard, name='lab_dashboard'),
    path('billing/', views.billing_dashboard, name='billing_dashboard'),
    path('inventory/', views.inventory_dashboard, name='inventory_dashboard'),
    path('hr/', views.hr_dashboard, name='hr_dashboard'),
    path('support/', views.support_dashboard, name='support_dashboard'),
]