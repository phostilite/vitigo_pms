# views.py

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.utils import timezone
from django.http import HttpResponse
from .models import Report, ReportExecution, Dashboard, DashboardWidget, AnalyticsLog
from django.db.models import Count

class ReportsAnalyticsManagementView(View):
    template_name = 'dashboard/admin/reports_analytics/reports_analytics_dashboard.html'

    def get(self, request):
        try:
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

            return render(request, self.template_name, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)