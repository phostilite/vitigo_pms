from django.urls import path
from .views import AssetDashboardView

urlpatterns = [
    path('dashboard/', AssetDashboardView.as_view(), name='asset_dashboard'),
]