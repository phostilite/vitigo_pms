from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Consultation, Prescription, TreatmentInstruction, ConsultationAttachment, FollowUpPlan

admin.site.register(Consultation)
admin.site.register(Prescription)
admin.site.register(TreatmentInstruction)
admin.site.register(ConsultationAttachment)
admin.site.register(FollowUpPlan)