from django.urls import path
from .views import (
    assets,
    dashboard,
    maintenance,
    audits,
    insurances,
)

urlpatterns = [
    path('dashboard/', dashboard.AssetDashboardView.as_view(), name='asset_dashboard'),
    
    path('asset/add/', assets.AddAssetView.as_view(), name='add_asset'),
    path('assets/total/', assets.TotalAssetsView.as_view(), name='total_assets'),
    
    path('maintenance/schedule/', maintenance.MaintenanceScheduleView.as_view(), name='maintenance_schedule'),
    path('maintenance/schedule/create/', maintenance.CreateMaintenanceScheduleView.as_view(), name='create_maintenance_schedule'),
    
    path('audits/total/', audits.TotalAuditsView.as_view(), name='total_audits'),
    
    path('insurances/total/', insurances.TotalInsurancesView.as_view(), name='total_insurances'),
]