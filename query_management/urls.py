from django.urls import path
from . import views

urlpatterns = [
    path('', views.QueryManagementView.as_view(), name='query_management'),
    path('create/', views.QueryCreateView.as_view(), name='query_create'),
    path('<int:query_id>/update/', views.QueryUpdateView.as_view(), name='query_update'),
    path('<int:query_id>/delete/', views.QueryDeleteView.as_view(), name='query_delete'),
    path('<int:query_id>/assign/', views.QueryAssignView.as_view(), name='query_assign'),
    path('<int:query_id>/', views.QueryDetailView.as_view(), name='query_detail'),
]