from django.urls import path
from . import views

urlpatterns = [
    path('', views.PhototherapyManagementView.as_view(), name='phototherapy_management'),
]