from django.urls import path, include
from django.conf import settings

from . import views

urlpatterns = [
    path('', views.PatientListView.as_view(), name='patient_list'),
    path('<int:patient_id>/', views.PatientDetailView.as_view(), name='patient_detail'),
]