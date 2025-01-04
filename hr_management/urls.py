from django.urls import path
from .views import (
    dashboard as dashboard_views,
    departments as department_views,
    employees as employee_views,
    leaves as leave_views,
    trainings as training_views,
    grievances as grievance_views,
    performance as performance_views,
    documents as document_views,
    notices as notice_views
)

urlpatterns = [
    path('', dashboard_views.HRManagementView.as_view(), name='hr_management'),
    
    path('new-employee/', employee_views.NewEmployeeView.as_view(), name='new_employee'),
    path('employees/', employee_views.EmployeeListView.as_view(), name='employee_list'),
    path('employees/bulk-actions/', employee_views.BulkActionsView.as_view(), name='employee_bulk_actions'),
    
    path('departments/', department_views.DepartmentListView.as_view(), name='department_list'),
    path('new-department/', department_views.NewDepartmentView.as_view(), name='new_department'),

    path('leaves/', leave_views.LeaveListView.as_view(), name='leave_list'),
    path('leaves/pending/', leave_views.PendingLeaveRequestsView.as_view(), name='pending_leave_requests'),
    path('leaves/calendar/', leave_views.LeaveCalendarView.as_view(), name='leave_calendar'),
    path('leaves/settings/', leave_views.LeaveSettingsView.as_view(), name='leave_settings'),
    
    path('trainings/', training_views.TrainingListView.as_view(), name='training_list'),
    path('trainings/schedule/', training_views.TrainingScheduleView.as_view(), name='training_schedule'),
    path('trainings/skill-matrix/', training_views.SkillMatrixView.as_view(), name='skill_matrix'),

    path('grievances/', grievance_views.GrievanceListView.as_view(), name='grievance_list'),
    
    path('performance/reviews/', performance_views.PerformanceListView.as_view(), name='performance_reviews'),

    path('documents/', document_views.DocumentListView.as_view(), name='document_list'),
    path('documents/upload/', document_views.DocumentUploadView.as_view(), name='document_upload'),

    path('notices/', notice_views.NoticeListView.as_view(), name='notice_list'),
]