# views.py

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.utils import timezone
from django.http import HttpResponse
from .models import Employee, Attendance, LeaveType, LeaveRequest, PerformanceReview, Training, TrainingAttendance
from django.db.models import Count, Sum

class HRManagementView(View):
    template_name = 'dashboard/admin/hr_management/hr_dashboard.html'

    def get(self, request):
        try:
            # Fetch all employees, attendance records, leave requests, performance reviews, and trainings
            employees = Employee.objects.all()
            attendance_records = Attendance.objects.all()
            leave_requests = LeaveRequest.objects.all()
            performance_reviews = PerformanceReview.objects.all()
            trainings = Training.objects.all()

            # Calculate statistics
            total_employees = employees.count()
            total_attendance = attendance_records.count()
            total_leave_requests = leave_requests.count()
            total_performance_reviews = performance_reviews.count()
            total_trainings = trainings.count()

            # Pagination for employees
            paginator = Paginator(employees, 10)  # Show 10 employees per page
            page = request.GET.get('page')
            try:
                employees = paginator.page(page)
            except PageNotAnInteger:
                employees = paginator.page(1)
            except EmptyPage:
                employees = paginator.page(paginator.num_pages)

            # Context data to be passed to the template
            context = {
                'employees': employees,
                'attendance_records': attendance_records,
                'leave_requests': leave_requests,
                'performance_reviews': performance_reviews,
                'trainings': trainings,
                'total_employees': total_employees,
                'total_attendance': total_attendance,
                'total_leave_requests': total_leave_requests,
                'total_performance_reviews': total_performance_reviews,
                'total_trainings': total_trainings,
                'paginator': paginator,
                'page_obj': employees,
            }

            return render(request, self.template_name, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)