from django.urls import path
from .views import (
    QueryManagementView, QueryDetailView, QueryCreateView, QueryUpdateView,
    QueryDeleteView, QueryAssignView, QueryUpdateStatusView, QueryResolveView,
    QueryTrendDataView, QueryResponseTimeDataView, QueryStaffPerformanceDataView
)

urlpatterns = [
    path('', QueryManagementView.as_view(), name='query_management'),
    path('create/', QueryCreateView.as_view(), name='query_create'),
    path('<int:query_id>/update/', QueryUpdateView.as_view(), name='query_update'),
    path('<int:query_id>/delete/', QueryDeleteView.as_view(), name='query_delete'),
    path('<int:query_id>/assign/', QueryAssignView.as_view(), name='query_assign'),
    path('<int:query_id>/update-status/', QueryUpdateStatusView.as_view(), name='query_update_status'),
    path('<int:query_id>/resolve/', QueryResolveView.as_view(), name='query_resolve'),
    path('<int:query_id>/', QueryDetailView.as_view(), name='query_detail'),
    path('trend-data/', QueryTrendDataView.as_view(), name='query_trend_data'),
    path('response-time-data/', QueryResponseTimeDataView.as_view(), name='query_response_time_data'),
    path('staff-performance-data/', QueryStaffPerformanceDataView.as_view(), name='query_staff_performance_data'),
]