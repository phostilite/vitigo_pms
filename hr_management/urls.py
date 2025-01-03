from django.urls import path
from .views import (
    dashboard as dashboard_views,
    departments as department_views,
    employees as employee_views,
    leaves as leave_views,
    trainings as training_views,
    grievances as grievance_views
)

urlpatterns = [
    path('', dashboard_views.HRManagementView.as_view(), name='hr_management'),
    
    path('new-employee/', employee_views.NewEmployeeView.as_view(), name='new_employee'),
    path('employees/', employee_views.EmployeeListView.as_view(), name='employee_list'),
    
    path('departments/', department_views.DepartmentListView.as_view(), name='department_list'),
    path('new-department/', department_views.NewDepartmentView.as_view(), name='new_department'),

    path('leaves/', leave_views.LeaveListView.as_view(), name='leave_list'),
    
    path('trainings/', training_views.TrainingListView.as_view(), name='training_list'),

    path('grievances/', grievance_views.GrievanceListView.as_view(), name='grievance_list'),
]