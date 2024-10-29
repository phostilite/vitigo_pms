from django.urls import path
from . import views

urlpatterns = [
    path('', views.QueryManagementView.as_view(), name='query_management'),
]