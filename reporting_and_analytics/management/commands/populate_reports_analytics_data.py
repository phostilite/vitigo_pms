# reporting_and_analytics/management/commands/populate_reports_analytics_data.py

import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from user_management.models import CustomUser
from reporting_and_analytics.models import (
    Report, ReportExecution, Dashboard, DashboardWidget, AnalyticsLog
)

class Command(BaseCommand):
    help = 'Generate sample reports and analytics data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating sample reports and analytics data...')

        # Fetch all users
        users = CustomUser.objects.all()

        # Create sample reports
        report_types = ['PATIENT', 'FINANCIAL', 'APPOINTMENT', 'TREATMENT', 'INVENTORY', 'HR', 'CUSTOM']
        for i in range(10):  # Generate 10 sample reports
            created_by = random.choice(users)
            report = Report.objects.create(
                name=f"Report {i + 1}",
                description='Sample report description',
                report_type=random.choice(report_types),
                query='SELECT * FROM sample_table',
                parameters={'param1': 'value1', 'param2': 'value2'},
                created_by=created_by,
                is_scheduled=random.choice([True, False]),
                frequency=random.choice(['DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY', 'ONE_TIME']),
                next_run=timezone.now() + timezone.timedelta(days=random.randint(1, 30)) if random.choice([True, False]) else None
            )

            # Create sample report executions
            for j in range(random.randint(1, 5)):  # Generate 1 to 5 executions per report
                ReportExecution.objects.create(
                    report=report,
                    executed_by=random.choice(users),
                    status=random.choice(['SUCCESS', 'FAILURE', 'IN_PROGRESS']),
                    result_file='path/to/result_file.pdf' if random.choice([True, False]) else None,
                    error_message='Sample error message' if random.choice([True, False]) else ''
                )

        # Create sample dashboards
        for i in range(5):  # Generate 5 sample dashboards
            created_by = random.choice(users)
            dashboard = Dashboard.objects.create(
                name=f"Dashboard {i + 1}",
                description='Sample dashboard description',
                created_by=created_by,
                is_public=random.choice([True, False])
            )

            # Create sample dashboard widgets
            widget_types = ['CHART', 'TABLE', 'METRIC', 'CUSTOM']
            for j in range(random.randint(1, 5)):  # Add 1 to 5 widgets to each dashboard
                DashboardWidget.objects.create(
                    dashboard=dashboard,
                    name=f"Widget {j + 1}",
                    widget_type=random.choice(widget_types),
                    data_source=random.choice(Report.objects.all()) if random.choice([True, False]) else None,
                    config={'key': 'value'},
                    position=j + 1
                )

        # Create sample analytics logs
        actions = ['Created Report', 'Executed Report', 'Created Dashboard', 'Updated Widget']
        for i in range(20):  # Generate 20 sample analytics logs
            AnalyticsLog.objects.create(
                user=random.choice(users),
                action=random.choice(actions),
                details={'detail_key': 'detail_value'},
                timestamp=timezone.now() - timezone.timedelta(days=random.randint(0, 30))
            )

        self.stdout.write(self.style.SUCCESS('Successfully generated sample reports and analytics data'))