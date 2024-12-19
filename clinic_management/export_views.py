from datetime import datetime, timedelta
import logging
from io import BytesIO
import xlsxwriter

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.utils import timezone
from django.views import View
from django.db.models import Count, Q
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from access_control.permissions import PermissionManager
from .models import ClinicVisit, VisitChecklist, VisitStatus, ClinicChecklist

logger = logging.getLogger(__name__)

class ClinicDashboardExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'clinic_management')

    def get(self, request):
        try:
            export_format = request.GET.get('format', 'excel')
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

        visits = ClinicVisit.objects.all()
        checklists = VisitChecklist.objects.all()
        statuses = VisitStatus.objects.all()

        return {
            'summary': {
                'total_active_visits': visits.filter(current_status__is_terminal_state=False).count(),
                'total_checklists': ClinicChecklist.objects.filter(is_active=True).count(),
                'status_types': statuses.count(),
                'completed_today': visits.filter(
                    completion_time__date=today.date(),
                    current_status__is_terminal_state=True
                ).count(),
                'monthly_visits': visits.filter(
                    visit_date__month=current_month,
                    visit_date__year=current_year
                ).count()
            },
            'visits': visits.order_by('-visit_date')[:10],
            'checklists': checklists.order_by('-completed_at')[:10],
            'statuses': statuses,
            'export_date': today
        }

    def export_excel(self, data):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'fg_color': '#4B5563',
            'font_color': 'white',
            'border': 1
        })
        cell_format = workbook.add_format({'border': 1})

        # Summary Sheet
        self._create_summary_sheet(workbook, data, header_format, cell_format)
        
        # Visits Sheet
        self._create_visits_sheet(workbook, data, header_format, cell_format)
        
        # Checklists Sheet
        self._create_checklists_sheet(workbook, data, header_format, cell_format)

        workbook.close()
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=clinic_dashboard.xlsx'
        return response

    def _create_summary_sheet(self, workbook, data, header_format, cell_format):
        sheet = workbook.add_worksheet('Summary')
        summary_data = [
            ['Metric', 'Value'],
            ['Active Visits', data['summary']['total_active_visits']],
            ['Active Checklists', data['summary']['total_checklists']],
            ['Status Types', data['summary']['status_types']],
            ['Completed Today', data['summary']['completed_today']],
            ['Monthly Visits', data['summary']['monthly_visits']]
        ]
        for row_num, row_data in enumerate(summary_data):
            for col_num, cell_value in enumerate(row_data):
                if row_num == 0:
                    sheet.write(row_num, col_num, cell_value, header_format)
                else:
                    sheet.write(row_num, col_num, cell_value, cell_format)

    def _create_visits_sheet(self, workbook, data, header_format, cell_format):
        sheet = workbook.add_worksheet('Recent Visits')
        headers = ['Visit Number', 'Patient', 'Date', 'Status', 'Priority']
        
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
            
        for row, visit in enumerate(data['visits'], start=1):
            sheet.write(row, 0, visit.visit_number, cell_format)
            sheet.write(row, 1, visit.patient.get_full_name(), cell_format)
            sheet.write(row, 2, visit.visit_date.strftime('%Y-%m-%d'), cell_format)
            sheet.write(row, 3, visit.current_status.display_name, cell_format)
            sheet.write(row, 4, dict(visit.PRIORITY_CHOICES)[visit.priority], cell_format)

    def _create_checklists_sheet(self, workbook, data, header_format, cell_format):
        sheet = workbook.add_worksheet('Recent Checklists')
        headers = ['Visit', 'Checklist', 'Completed By', 'Completed At']
        
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
            
        for row, checklist in enumerate(data['checklists'], start=1):
            sheet.write(row, 0, checklist.visit.visit_number, cell_format)
            sheet.write(row, 1, checklist.checklist.name, cell_format)
            sheet.write(row, 2, checklist.completed_by.get_full_name() if checklist.completed_by else 'N/A', cell_format)
            sheet.write(row, 3, checklist.completed_at.strftime('%Y-%m-%d %H:%M'), cell_format)

    def export_pdf(self, data):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=clinic_dashboard.pdf'

        doc = SimpleDocTemplate(response, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()

        # Title
        elements.append(Paragraph('Clinic Management Dashboard Report', styles['Heading1']))
        elements.append(Spacer(1, 20))

        # Summary Table
        elements.append(Paragraph('Summary Statistics', styles['Heading2']))
        summary_data = [
            ['Metric', 'Value'],
            ['Active Visits', str(data['summary']['total_active_visits'])],
            ['Active Checklists', str(data['summary']['total_checklists'])],
            ['Status Types', str(data['summary']['status_types'])],
            ['Completed Today', str(data['summary']['completed_today'])],
            ['Monthly Visits', str(data['summary']['monthly_visits'])]
        ]
        summary_table = Table(summary_data, colWidths=[200, 100])
        summary_table.setStyle(self.get_table_style())
        elements.append(summary_table)
        elements.append(Spacer(1, 20))

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
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
