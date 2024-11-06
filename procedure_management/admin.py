from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import ProcedureType, Procedure, ConsentForm, ProcedureResult, ProcedureImage

admin.site.register(ProcedureType)
admin.site.register(ProcedureImage)
admin.site.register(ConsentForm)
admin.site.register(ProcedureResult)
admin.site.register(Procedure)