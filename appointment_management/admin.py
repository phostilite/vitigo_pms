from django.contrib import admin
from .models import TimeSlot, Appointment, AppointmentReminder, CancellationReason

admin.site.register(TimeSlot)
admin.site.register(Appointment)
admin.site.register(AppointmentReminder)
admin.site.register(CancellationReason)
