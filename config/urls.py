from django.urls import path, include

urlpatterns = [
    # ... other URL patterns ...
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('users/', include('user_management.urls', namespace='user_management')),
]
