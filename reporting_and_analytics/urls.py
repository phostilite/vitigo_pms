# urls.py

from django.urls import path
from . import views

app_name = 'reporting_and_analytics'

urlpatterns = [
    path('', views.ReportsAnalyticsManagementView.as_view(), name='reports_analytics_management'),
    path('category/<int:category_id>/reports/', 
         views.CategoryReportsView.as_view(), 
         name='category_reports'),
]