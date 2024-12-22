from django.urls import path
from .views import SettingsManagementView

urlpatterns = [
    path('', SettingsManagementView.as_view(), name='settings_management'),
]