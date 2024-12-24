from django.urls import path
from .views import views as v
from .views import core as c

app_name = 'settings'

urlpatterns = [
    path('', v.SettingsManagementView.as_view(), name='settings_dashboard'),
    path('core/', c.CoreSettingsView.as_view(), name='core_settings'),
]