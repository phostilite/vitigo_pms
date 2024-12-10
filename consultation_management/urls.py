# URLs configuration (add to urls.py)
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ConsultationDashboardView.as_view(), name='consultation_dashboard'),
    path('create/', views.ConsultationCreateView.as_view(), name='consultation_create'),
    path('delete/<int:consultation_id>/', views.ConsultationDeleteView.as_view(), name='consultation_delete'),

]