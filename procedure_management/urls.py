from django.urls import path
from .views import ProcedureManagementView, ProcedureDetailView

urlpatterns = [
    path('', ProcedureManagementView.as_view(), name='procedure_management'),
    path('<int:procedure_id>/', ProcedureDetailView.as_view(), name='procedure_detail'),
]