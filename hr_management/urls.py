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
    path('employees/<int:pk>/', employee_views.EmployeeDetailView.as_view(), name='employee_detail'),
    path('employees/<int:pk>/edit/', employee_views.EmployeeEditView.as_view(), name='employee_edit'),
    path('employees/<int:pk>/delete/', employee_views.EmployeeDeleteView.as_view(), name='employee_delete'),
    path('employees/bulk-actions/', employee_views.BulkActionsView.as_view(), name='employee_bulk_actions'),
    
    path('departments/', department_views.DepartmentListView.as_view(), name='department_list'),
    path('new-department/', department_views.NewDepartmentView.as_view(), name='new_department'),
    path('departments/<int:pk>/', department_views.DepartmentDetailView.as_view(), name='department_detail'),
    path('departments/<int:pk>/edit/', department_views.DepartmentEditView.as_view(), name='department_edit'),
    path('departments/<int:pk>/delete/', department_views.DepartmentDeleteView.as_view(), name='department_delete'),

    path('leaves/', leave_views.LeaveListView.as_view(), name='leave_list'),
    path('leaves/pending/', leave_views.PendingLeaveRequestsView.as_view(), name='pending_leave_requests'),
    path('leaves/calendar/', leave_views.LeaveCalendarView.as_view(), name='leave_calendar'),
    path('leaves/settings/', leave_views.LeaveSettingsView.as_view(), name='leave_settings'),
    path('leaves/<int:pk>/', leave_views.LeaveDetailView.as_view(), name='leave_detail'),
    path('leaves/<int:pk>/<str:action>/', leave_views.LeaveActionView.as_view(), name='leave_action'),
    
    path('trainings/', training_views.TrainingListView.as_view(), name='training_list'),
    path('trainings/schedule/', training_views.TrainingScheduleView.as_view(), name='training_schedule'),
    path('trainings/skill-matrix/', training_views.SkillMatrixView.as_view(), name='skill_matrix'),
    path('trainings/new/', training_views.NewTrainingView.as_view(), name='new_training'),
    path('trainings/<int:pk>/', training_views.TrainingDetailView.as_view(), name='training_detail'),

    path('grievances/', grievance_views.GrievanceListView.as_view(), name='grievance_list'),
    
    path('performance/reviews/', performance_views.PerformanceListView.as_view(), name='performance_reviews'),

    path('documents/', document_views.DocumentListView.as_view(), name='document_list'),
    path('documents/upload/', document_views.DocumentUploadView.as_view(), name='document_upload'),

    path('notices/', notice_views.NoticeListView.as_view(), name='notice_list'),
    path('notices/new/', notice_views.NoticeCreateView.as_view(), name='notice_create'),
]