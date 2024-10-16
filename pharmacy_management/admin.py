from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Medication, MedicationStock, Supplier, PurchaseOrder, PurchaseOrderItem, Prescription, \
    PrescriptionItem


class MedicationStockInline(admin.StackedInline):
    model = MedicationStock
    can_delete = False
    verbose_name_plural = 'Medication Stock'


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'dosage_form', 'strength', 'price', 'requires_prescription', 'is_active')
    list_filter = ('dosage_form', 'requires_prescription', 'is_active', 'manufacturer')
    search_fields = ('name', 'generic_name', 'description')
    inlines = [MedicationStockInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'generic_name', 'description', 'dosage_form', 'strength', 'manufacturer')
        }),
        ('Pricing and Availability', {
            'fields': ('price', 'requires_prescription', 'is_active')
        }),
    )


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'contact_person', 'email')


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'order_date', 'status', 'total_amount', 'expected_delivery_date', 'received_date')
    list_filter = ('status', 'order_date', 'expected_delivery_date', 'received_date')
    search_fields = ('supplier__name', 'created_by__email')
    inlines = [PurchaseOrderItemInline]

    fieldsets = (
        (None, {
            'fields': ('supplier', 'status', 'total_amount', 'expected_delivery_date', 'received_date', 'created_by')
        }),
    )


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient_link', 'doctor_link', 'prescription_date', 'status', 'filled_by', 'filled_date')
    list_filter = ('status', 'prescription_date', 'filled_date')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'doctor__email', 'filled_by__email')
    inlines = [PrescriptionItemInline]

    fieldsets = (
        (None, {
            'fields': ('patient', 'doctor', 'status', 'notes', 'filled_by', 'filled_date')
        }),
    )

    def patient_link(self, obj):
        url = reverse("admin:patient_management_patient_change", args=[obj.patient.id])
        return format_html('<a href="{}">{}</a>', url, obj.patient.user.get_full_name())

    patient_link.short_description = 'Patient'

    def doctor_link(self, obj):
        url = reverse("admin:user_management_customuser_change", args=[obj.doctor.id])
        return format_html('<a href="{}">{}</a>', url, obj.doctor.get_full_name())

    doctor_link.short_description = 'Doctor'


@admin.register(MedicationStock)
class MedicationStockAdmin(admin.ModelAdmin):
    list_display = ('medication', 'quantity', 'reorder_level', 'last_restocked')
    list_filter = ('last_restocked',)
    search_fields = ('medication__name', 'medication__generic_name')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('medication',)
        return self.readonly_fields


# Registering the through model for many-to-many relationships
admin.site.register(PurchaseOrderItem)
admin.site.register(PrescriptionItem)