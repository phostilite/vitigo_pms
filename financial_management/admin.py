from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Invoice, InvoiceItem, Payment, Expense, FinancialReport

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'patient_link', 'status', 'issue_date', 'due_date', 'total_amount', 'created_by')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('invoice_number', 'patient__user__first_name', 'patient__user__last_name', 'patient__user__email')
    inlines = [InvoiceItemInline, PaymentInline]
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('patient', 'invoice_number', 'status', 'issue_date', 'due_date')
        }),
        ('Financial Details', {
            'fields': ('total_amount', 'discount', 'tax')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at')
        }),
    )

    def patient_link(self, obj):
        url = reverse("admin:patient_management_patient_change", args=[obj.patient.id])
        return format_html('<a href="{}">{}</a>', url, obj.patient.user.get_full_name())
    patient_link.short_description = 'Patient'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice_link', 'amount', 'payment_date', 'payment_method', 'transaction_id', 'received_by')
    list_filter = ('payment_date', 'payment_method')
    search_fields = ('invoice__invoice_number', 'transaction_id', 'notes')

    def invoice_link(self, obj):
        url = reverse("admin:financial_management_invoice_change", args=[obj.invoice.id])
        return format_html('<a href="{}">{}</a>', url, obj.invoice.invoice_number)
    invoice_link.short_description = 'Invoice'

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'date', 'paid_to', 'payment_method', 'approved_by', 'created_by')
    list_filter = ('category', 'date', 'payment_method')
    search_fields = ('description', 'paid_to')
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('category', 'amount', 'date', 'description', 'paid_to', 'payment_method')
        }),
        ('Documentation', {
            'fields': ('receipt',)
        }),
        ('Approval', {
            'fields': ('approved_by', 'created_by', 'created_at')
        }),
    )

@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'start_date', 'end_date', 'total_revenue', 'total_expenses', 'net_profit', 'generated_by', 'generated_at')
    list_filter = ('report_type', 'start_date', 'end_date')
    search_fields = ('report_type', 'generated_by__email')
    readonly_fields = ('generated_at',)

    fieldsets = (
        (None, {
            'fields': ('report_type', 'start_date', 'end_date')
        }),
        ('Financial Summary', {
            'fields': ('total_revenue', 'total_expenses', 'net_profit')
        }),
        ('Report Details', {
            'fields': ('report_file', 'generated_by', 'generated_at')
        }),
    )

# Customize admin site
admin.site.site_header = "VitiGo Financial Management"
admin.site.site_title = "VitiGo Finance Admin"
admin.site.index_title = "Welcome to VitiGo Financial Management System"