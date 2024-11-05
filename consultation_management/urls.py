# URLs configuration (add to urls.py)
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ConsultationManagementView.as_view(), name='consultation_management'),
    path('<int:pk>/', views.ConsultationDetailView.as_view(), name='consultation_detail'),
]