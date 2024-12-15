from datetime import datetime
import logging
from io import BytesIO
import xlsxwriter

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.utils import timezone
from django.views import View
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from access_control.permissions import PermissionManager
from .models import (
    PhototherapyPlan, PhototherapySession, PhototherapyDevice,
    PhototherapyType, PhototherapyPayment, PhototherapyProgress
)

logger = logging.getLogger(__name__)

class PhototherapyDashboardExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'phototherapy_management')

    def get(self, request):
        try:
            export_format = request.GET.get('format', 'excel')
            
            # Collect all necessary data
            data = self.gather_dashboard_data()
            
            if export_format == 'excel':
                return self.export_excel(data)
            elif export_format == 'pdf':
                return self.export_pdf(data)
            else:
                return HttpResponse('Invalid format specified', status=400)
        except Exception as e:
            logger.error(f"Export error: {str(e)}")
            return HttpResponse('Export failed', status=500)

    def gather_dashboard_data(self):
        """Gather all dashboard metrics and data"""
        today = timezone.now()
        current_month = today.month
        current_year = today.year

        plans = PhototherapyPlan.objects.all()
        sessions = PhototherapySession.objects.all()
        devices = PhototherapyDevice.objects.all()
        payments = PhototherapyPayment.objects.filter(status='COMPLETED')

        return {
            'summary': {
                'total_active_plans': plans.filter(is_active=True).count(),
                'total_completed_sessions': sessions.filter(status='COMPLETED').count(),
                'total_missed_sessions': sessions.filter(status='MISSED').count(),
                'active_devices': devices.filter(is_active=True).count(),
                'maintenance_needed': devices.filter(
                    next_maintenance_date__lte=today.date()
                ).count(),
                'monthly_sessions': sessions.filter(
                    scheduled_date__month=current_month,
                    scheduled_date__year=current_year
                ).count(),
                'monthly_revenue': payments.filter(
                    payment_date__month=current_month,
                    payment_date__year=current_year
                ).count()
            },
            'therapy_types': PhototherapyType.objects.all(),
            'recent_sessions': sessions.order_by('-scheduled_date')[:10],
            'recent_payments': payments.order_by('-payment_date')[:10],
            'progress_stats': PhototherapyProgress.objects.all()
        }

    def export_excel(self, data):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        # Styles
        header_format = workbook.add_format({
            'bold': True,
            'fg_color': '#4B5563',
            'font_color': 'white',
            'border': 1
        })
        cell_format = workbook.add_format({'border': 1})
        
        # Summary Sheet
        summary_sheet = workbook.add_worksheet('Dashboard Summary')
        summary_data = [
            ['Metric', 'Value'],
            ['Active Treatment Plans', data['summary']['total_active_plans']],
            ['Completed Sessions', data['summary']['total_completed_sessions']],
            ['Missed Sessions', data['summary']['total_missed_sessions']],
            ['Active Devices', data['summary']['active_devices']],
            ['Devices Needing Maintenance', data['summary']['maintenance_needed']],
            ['Sessions This Month', data['summary']['monthly_sessions']],
            ['Monthly Revenue', data['summary']['monthly_revenue']]
        ]
        self.write_sheet_data(summary_sheet, summary_data, header_format, cell_format)

        # Recent Sessions Sheet
        sessions_sheet = workbook.add_worksheet('Recent Sessions')
        sessions_data = [['Date', 'Patient', 'Type', 'Status', 'Duration']]
        for session in data['recent_sessions']:
            sessions_data.append([
                session.scheduled_date.strftime('%Y-%m-%d'),
                session.plan.patient.get_full_name(),
                session.plan.protocol.phototherapy_type.name,
                session.get_status_display(),
                f"{session.duration_seconds/60:.0f} min" if session.duration_seconds else 'N/A'
            ])
        self.write_sheet_data(sessions_sheet, sessions_data, header_format, cell_format)

        # Recent Payments Sheet
        payments_sheet = workbook.add_worksheet('Recent Payments')
        payments_data = [['Date', 'Amount', 'Method', 'Status']]
        for payment in data['recent_payments']:
            payments_data.append([
                payment.payment_date.strftime('%Y-%m-%d'),
                f"${payment.amount}",
                payment.get_payment_method_display(),
                payment.get_status_display()
            ])
        self.write_sheet_data(payments_sheet, payments_data, header_format, cell_format)

        workbook.close()
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=phototherapy_dashboard.xlsx'
        return response

    def write_sheet_data(self, sheet, data, header_format, cell_format):
        for row_num, row_data in enumerate(data):
            for col_num, cell_value in enumerate(row_data):
                if row_num == 0:
                    sheet.write(row_num, col_num, cell_value, header_format)
                else:
                    sheet.write(row_num, col_num, cell_value, cell_format)
        sheet.set_column(0, len(data[0])-1, 15)  # Set column width

    def export_pdf(self, data):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=phototherapy_dashboard.pdf'

        doc = SimpleDocTemplate(response, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']

        # Title
        elements.append(Paragraph('Phototherapy Dashboard Report', title_style))
        elements.append(Paragraph(f'Generated on: {timezone.now().strftime("%Y-%m-%d %H:%M")}', styles['Normal']))
        elements.append(Spacer(1, 20))

        # Summary Statistics
        elements.append(Paragraph('Summary Statistics', subtitle_style))
        summary_data = [
            ['Metric', 'Value'],
            ['Active Treatment Plans', str(data['summary']['total_active_plans'])],
            ['Completed Sessions', str(data['summary']['total_completed_sessions'])],
            ['Missed Sessions', str(data['summary']['total_missed_sessions'])],
            ['Active Devices', str(data['summary']['active_devices'])],
            ['Devices Needing Maintenance', str(data['summary']['maintenance_needed'])],
            ['Sessions This Month', str(data['summary']['monthly_sessions'])],
            ['Monthly Revenue', f"${data['summary']['monthly_revenue']}"]
        ]
        summary_table = Table(summary_data, colWidths=[300, 200])
        summary_table.setStyle(self.get_table_style())
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        # Recent Sessions
        elements.append(Paragraph('Recent Sessions', subtitle_style))
        sessions_data = [['Date', 'Patient', 'Type', 'Status']]
        for session in data['recent_sessions']:
            sessions_data.append([
                session.scheduled_date.strftime('%Y-%m-%d'),
                session.plan.patient.get_full_name(),
                session.plan.protocol.phototherapy_type.name,
                session.get_status_display()
            ])
        sessions_table = Table(sessions_data, colWidths=[100, 200, 150, 100])
        sessions_table.setStyle(self.get_table_style())
        elements.append(sessions_table)

        doc.build(elements)
        return response

    def get_table_style(self):
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ])
