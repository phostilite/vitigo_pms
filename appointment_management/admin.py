from django.contrib import admin
from .models import Appointment, AppointmentReminder, CancellationReason, TimeSlotConfig, DoctorTimeSlot, ReminderConfiguration, ReminderTemplate

admin.site.register(Appointment)
admin.site.register(AppointmentReminder)
admin.site.register(CancellationReason)
admin.site.register(TimeSlotConfig)
admin.site.register(DoctorTimeSlot)
admin.site.register(ReminderConfiguration)
admin.site.register(ReminderTemplate)
