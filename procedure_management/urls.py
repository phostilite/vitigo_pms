from django.urls import path
from .views import (
    dashboard as dashboard_views,
    procedures as procedure_views,
)

app_name = 'procedure_management'

urlpatterns = [
    path('', dashboard_views.ProcedureManagementView.as_view(), name='procedure_management'),
    
    path('procedures/', procedure_views.ProcedureListView.as_view(), name='procedure_list'),
]