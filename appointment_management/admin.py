from django.contrib import admin
from .models import Appointment, AppointmentReminder, CancellationReason, TimeSlotConfig, DoctorTimeSlot

admin.site.register(Appointment)
admin.site.register(AppointmentReminder)
admin.site.register(CancellationReason)
admin.site.register(TimeSlotConfig)
admin.site.register(DoctorTimeSlot)
