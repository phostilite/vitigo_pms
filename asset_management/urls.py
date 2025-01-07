from django.urls import path
from .views import AssetDashboardView, AddAssetView

urlpatterns = [
    path('dashboard/', AssetDashboardView.as_view(), name='asset_dashboard'),
    
    path('asset/add/', AddAssetView.as_view(), name='add_asset'),
]