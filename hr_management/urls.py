from django.urls import path
from . import views

urlpatterns = [
    path('', views.HRManagementView.as_view(), name='hr_management'),
    path('new-employee/', views.NewEmployeeView.as_view(), name='new_employee'),
    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
]