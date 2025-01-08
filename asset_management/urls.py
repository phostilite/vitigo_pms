from django.urls import path
from .views import AssetDashboardView, AddAssetView, TotalAssetsView

urlpatterns = [
    path('dashboard/', AssetDashboardView.as_view(), name='asset_dashboard'),
    path('asset/add/', AddAssetView.as_view(), name='add_asset'),
    path('assets/total/', TotalAssetsView.as_view(), name='total_assets'),
]