from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProcedureManagementView.as_view(), name='procedure_management'),
]