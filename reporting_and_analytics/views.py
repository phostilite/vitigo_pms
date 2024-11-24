# views.py

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.utils import timezone
from django.http import HttpResponse
from .models import Report, ReportExecution, Dashboard, DashboardWidget, AnalyticsLog
from django.db.models import Count
from access_control.models import Role

def get_template_path(base_template, role, module=''):
    """
    Resolves template path based on user role.
    Now uses the template_folder from Role model.
    """
    if isinstance(role, Role):
        role_folder = role.template_folder
    else:
        # Fallback for any legacy code
        role = Role.objects.get(name=role)
        role_folder = role.template_folder
    
    if module:
        return f'dashboard/{role_folder}/{module}/{base_template}'
    return f'dashboard/{role_folder}/{base_template}'

class ReportsAnalyticsManagementView(View):
    def get_template_name(self):
        return get_template_path('reports_analytics_dashboard.html', self.request.user.role, 'reports_analytics')

    def get(self, request):
        try:
            template_path = self.get_template_name()
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)

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
                'user_role': request.user.role,  # Add user role to context
            }

            return render(request, template_path, context)

        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}", status=500)