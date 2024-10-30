from django.urls import path
from . import views

urlpatterns = [
    path('', views.SettingsManagementView.as_view(), name='settings_management'),
]