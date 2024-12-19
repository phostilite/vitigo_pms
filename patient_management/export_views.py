import logging
from io import BytesIO
import xlsxwriter
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from user_management.models import CustomUser
from .models import Patient, MedicalHistory, VitiligoAssessment, TreatmentPlan, Medication

logger = logging.getLogger(__name__)

class PatientDataExportView(LoginRequiredMixin, View):
    def get(self, request, user_id):
        try:
            user = get_object_or_404(CustomUser, id=user_id)
            patient = get_object_or_404(Patient, user=user)
            export_format = request.GET.get('format', 'excel')
            
            if export_format == 'pdf':
                return self.export_pdf(user, patient)
            return self.export_excel(user, patient)
            
        except Exception as e:
            logger.error(f"Error exporting patient data: {str(e)}")
            return HttpResponse('Export failed', status=500)

    def export_excel(self, user, patient):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4B5563',
            'font_color': 'white',
            'border': 1
        })
        cell_format = workbook.add_format({'border': 1})

        # Personal Information Sheet
        self._create_personal_info_sheet(workbook, user, patient, header_format, cell_format)
        
        # Medical History Sheet
        self._create_medical_history_sheet(workbook, patient, header_format, cell_format)
        
        # Assessments Sheet
        self._create_assessments_sheet(workbook, patient, header_format, cell_format)
        
        # Treatments Sheet
        self._create_treatments_sheet(workbook, patient, header_format, cell_format)

        workbook.close()
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=patient_data_{user.id}_{datetime.now().strftime("%Y%m%d")}.xlsx'
        return response

    def _create_personal_info_sheet(self, workbook, user, patient, header_format, cell_format):
        sheet = workbook.add_worksheet('Personal Information')
        data = [
            ['Field', 'Value'],
            ['Full Name', user.get_full_name()],
            ['Email', user.email],
            ['Phone', f"{user.country_code} {user.phone_number}"],
            ['Gender', user.get_gender_display()],
            ['Date of Birth', patient.date_of_birth.strftime('%Y-%m-%d')],
            ['Blood Group', patient.blood_group],
            ['Address', patient.address],
            ['Emergency Contact', f"{patient.emergency_contact_name} ({patient.emergency_contact_number})"],
        ]
        
        for row_num, row_data in enumerate(data):
            for col_num, cell_value in enumerate(row_data):
                if row_num == 0:
                    sheet.write(row_num, col_num, cell_value, header_format)
                else:
                    sheet.write(row_num, col_num, cell_value, cell_format)

    def _create_medical_history_sheet(self, workbook, patient, header_format, cell_format):
        sheet = workbook.add_worksheet('Medical History')
        try:
            history = patient.medical_history
            data = [
                ['Category', 'Details'],
                ['Allergies', history.allergies],
                ['Chronic Conditions', history.chronic_conditions],
                ['Past Surgeries', history.past_surgeries],
                ['Family History', history.family_history],
            ]
        except MedicalHistory.DoesNotExist:
            data = [['No medical history available']]

        for row_num, row_data in enumerate(data):
            for col_num, cell_value in enumerate(row_data):
                if row_num == 0:
                    sheet.write(row_num, col_num, cell_value, header_format)
                else:
                    sheet.write(row_num, col_num, cell_value, cell_format)

    def _create_assessments_sheet(self, workbook, patient, header_format, cell_format):
        sheet = workbook.add_worksheet('Vitiligo Assessments')
        headers = ['Date', 'BSA Score', 'VASI Score', 'Notes']
        sheet.write_row(0, 0, headers, header_format)

        assessments = VitiligoAssessment.objects.filter(patient=patient).order_by('-assessment_date')
        for row, assessment in enumerate(assessments, start=1):
            sheet.write(row, 0, assessment.assessment_date.strftime('%Y-%m-%d'), cell_format)
            sheet.write(row, 1, assessment.bsa_score, cell_format)
            sheet.write(row, 2, assessment.vasi_score, cell_format)
            sheet.write(row, 3, assessment.notes or '', cell_format)

    def _create_treatments_sheet(self, workbook, patient, header_format, cell_format):
        sheet = workbook.add_worksheet('Treatments & Medications')
        headers = ['Start Date', 'End Date', 'Treatment/Medication', 'Dosage', 'Notes']
        sheet.write_row(0, 0, headers, header_format)

        row = 1
        # Add treatments
        for treatment in TreatmentPlan.objects.filter(patient=patient).order_by('-created_date'):
            sheet.write(row, 0, treatment.created_date.strftime('%Y-%m-%d'), cell_format)
            sheet.write(row, 1, treatment.end_date.strftime('%Y-%m-%d') if treatment.end_date else 'Ongoing', cell_format)
            sheet.write(row, 2, treatment.treatment_type, cell_format)
            sheet.write(row, 3, 'N/A', cell_format)
            sheet.write(row, 4, treatment.notes or '', cell_format)
            row += 1

        # Add medications
        for medication in Medication.objects.filter(patient=patient).order_by('-start_date'):
            sheet.write(row, 0, medication.start_date.strftime('%Y-%m-%d'), cell_format)
            sheet.write(row, 1, medication.end_date.strftime('%Y-%m-%d') if medication.end_date else 'Ongoing', cell_format)
            sheet.write(row, 2, medication.name, cell_format)
            sheet.write(row, 3, medication.dosage, cell_format)
            sheet.write(row, 4, medication.notes or '', cell_format)
            row += 1

    def export_pdf(self, user, patient):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=patient_data_{user.id}_{datetime.now().strftime("%Y%m%d")}.pdf'

        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        elements.append(Paragraph(f'Patient Data: {user.get_full_name()}', styles['Heading1']))
        elements.append(Spacer(1, 20))

        # Personal Information
        elements.append(Paragraph('Personal Information', styles['Heading2']))
        personal_data = [
            ['Field', 'Value'],
            ['Full Name', user.get_full_name()],
            ['Email', user.email],
            ['Phone', f"{user.country_code} {user.phone_number}"],
            ['Gender', user.get_gender_display()],
            ['Date of Birth', patient.date_of_birth.strftime('%Y-%m-%d')],
        ]
        personal_table = Table(personal_data, colWidths=[200, 300])
        personal_table.setStyle(self._get_table_style())
        elements.append(personal_table)
        elements.append(Spacer(1, 20))

        # Add other sections similarly...

        doc.build(elements)
        return response

    def _get_table_style(self):
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ])
