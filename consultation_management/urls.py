# URLs configuration (add to urls.py)
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ConsultationDashboardView.as_view(), name='consultation_dashboard'),
    path('create/', views.ConsultationCreateView.as_view(), name='consultation_create'),
    path('<int:pk>/', views.ConsultationDetailView.as_view(), name='consultation_detail'),
    path('delete/<int:consultation_id>/', views.ConsultationDeleteView.as_view(), name='consultation_delete'),
    path('update-status/<int:pk>/', views.ConsultationStatusUpdateView.as_view(), name='consultation_status_update'),
    path('staff-instructions/<int:pk>/', views.StaffInstructionsUpdateView.as_view(), name='staff_instructions_update'),
]