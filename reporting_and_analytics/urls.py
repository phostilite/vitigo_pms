# urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.ReportsAnalyticsManagementView.as_view(), name='reports_analytics_management'),
]