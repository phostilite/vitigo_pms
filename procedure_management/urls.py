from django.urls import path
from .views import (
    dashboard as dashboard_views,
    procedures as procedure_views,
)

app_name = 'procedure_management'

urlpatterns = [
    # Dashboard URL
    path('', dashboard_views.ProcedureManagementView.as_view(), name='procedure_management'),
    
    # Procedure URLs
    path('procedures/', procedure_views.ProcedureListView.as_view(), name='procedure_list'),
    path('procedures/create/', procedure_views.ProcedureCreateView.as_view(), name='procedure_create'),
    path('procedures/<int:pk>/', procedure_views.ProcedureDetailView.as_view(), name='procedure_detail'),
    path('procedures/<int:pk>/edit/', procedure_views.ProcedureUpdateView.as_view(), name='procedure_update'),
    path('procedures/<int:pk>/delete/', procedure_views.ProcedureDeleteView.as_view(), name='procedure_delete'),
]