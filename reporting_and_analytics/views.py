# views.py

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.utils import timezone
from django.http import HttpResponse
from .models import Report, ReportExecution, Dashboard, DashboardWidget, AnalyticsLog
from django.db.models import Count

def get_template_path(base_template, user_role):
    """
    Resolves template path based on user role.
    Example: For 'reports_analytics_dashboard.html' and role 'ACCOUNTANT', 
    returns 'dashboard/accountant/reports_analytics/reports_analytics_dashboard.html'
    """
    role_template_map = {
        'ADMIN': 'admin',
        'DOCTOR': 'doctor',
        'NURSE': 'nurse',
        'RECEPTIONIST': 'receptionist',
        'PHARMACIST': 'pharmacist',
        'LAB_TECHNICIAN': 'lab',
        'ACCOUNTANT': 'accountant',
        'MANAGER': 'manager',
        'TECHNICIAN': 'technician',
        'ASSISTANT': 'assistant',
        'SUPERVISOR': 'supervisor',
    }
    
    role_folder = role_template_map.get(user_role)
    if not role_folder:
        return None
    return f'dashboard/{role_folder}/reports_analytics/{base_template}'

class ReportsAnalyticsManagementView(View):
    def get(self, request):
        try:
            user_role = request.user.role  # Assuming user role is stored in request.user.role
            template_name = get_template_path('reports_analytics_dashboard.html', user_role)
            if not template_name:
                return HttpResponse("User role does not have a corresponding template.", status=403)

            # Fetch all reports, report executions, dashboards, dashboard widgets, and analytics logs
            reports = Report.objects.all()
            report_executions = ReportExecution.objects.all()
            dashboards = Dashboard.objects.all()
            dashboard_widgets = DashboardWidget.objects.all()
            analytics_logs = AnalyticsLog.objects.all()

            # Calculate statistics
            total_reports = reports.count()
            total_executions = report_executions.count()
            total_dashboards = dashboards.count()
            total_widgets = dashboard_widgets.count()
            total_logs = analytics_logs.count()

            # Pagination for reports
            paginator = Paginator(reports, 10)  # Show 10 reports per page
            page = request.GET.get('page')
            try:
                reports = paginator.page(page)
            except PageNotAnInteger:
                reports = paginator.page(1)
            except EmptyPage:
                reports = paginator.page(paginator.num_pages)

            # Context data to be passed to the template
            context = {
                'reports': reports,
                'report_executions': report_executions,
                'dashboards': dashboards,
                'dashboard_widgets': dashboard_widgets,
                'analytics_logs': analytics_logs,
                'total_reports': total_reports,
                'total_executions': total_executions,
                'total_dashboards': total_dashboards,
                'total_widgets': total_widgets,
                'total_logs': total_logs,
                'paginator': paginator,
                'page_obj': reports,
            }

            return render(request, template_name, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)