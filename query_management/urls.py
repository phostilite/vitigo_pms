from django.urls import path
from .views import QueryManagementView, QueryDetailView

urlpatterns = [
    path('', QueryManagementView.as_view(), name='query_management'),
    path('<int:query_id>/', QueryDetailView.as_view(), name='query_detail'),
]