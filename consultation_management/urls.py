# URLs configuration (add to urls.py)
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ConsultationDashboardView.as_view(), name='consultation_management'),
    path('delete/<int:consultation_id>/', views.ConsultationDeleteView.as_view(), name='consultation_delete'),
]