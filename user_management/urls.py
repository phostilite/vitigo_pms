# user_management/urls.py
from django.urls import path
from . import views
from .views import UserExportView

urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('', views.UserManagementView.as_view(), name='user_management'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('create/', views.CreateUserView.as_view(), name='create_user'),
    path('<int:user_id>/', views.UserDetailsView.as_view(), name='user_detail'),
    path('<int:user_id>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('delete/<int:user_id>/', views.UserDeleteView.as_view(), name='user_delete'),
    path('deactivate/<int:user_id>/', views.UserDeactivateView.as_view(), name='user_deactivate'),
    path('reset-password/<int:user_id>/', views.UserResetPasswordView.as_view(), name='user_reset_password'),
    path('export/', UserExportView.as_view(), name='user_export'),
]