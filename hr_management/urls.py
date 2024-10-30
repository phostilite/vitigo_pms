from django.urls import path
from . import views

urlpatterns = [
    path('', views.HRManagementView.as_view(), name='hr_management'),
]