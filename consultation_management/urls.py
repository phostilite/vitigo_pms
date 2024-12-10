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
    path('prescriptions/', views.PrescriptionDashboardView.as_view(), name='prescription_dashboard'),
    path('prescription/create/<int:consultation_id>/', views.PrescriptionCreateView.as_view(), name='create_prescription'),
    path('prescription/use-template/<int:consultation_id>/<int:template_id>/', 
         views.UsePrescriptionTemplateView.as_view(), 
         name='use_prescription_template'),
    path('prescription/edit/<int:consultation_id>/<int:prescription_id>/',
         views.PrescriptionEditView.as_view(),
         name='edit_prescription'),
    path('prescriptions/template/create/', views.PrescriptionTemplateCreateView.as_view(), name='create_prescription_template'),
    path('prescriptions/template/<int:pk>/edit/', views.PrescriptionTemplateEditView.as_view(), name='edit_prescription_template'),
    path('prescriptions/template/<int:pk>/delete/', views.PrescriptionTemplateDeleteView.as_view(), name='delete_prescription_template'),
    path('export/', views.ConsultationExportView.as_view(), name='consultation_export'),
]