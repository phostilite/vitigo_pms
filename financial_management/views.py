# views.py

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.utils import timezone
from django.http import HttpResponse
from .models import GSTRate, Invoice, Payment, Expense, TDSEntry, FinancialYear, FinancialReport
from django.db.models import Sum
from access_control.models import Role

def get_template_path(base_template, role, module=''):
    """
    Resolves template path based on user role.
    Now uses the template_folder from Role model.
    """
    if isinstance(role, Role):
        role_folder = role.template_folder
    else:
        # Fallback for any legacy code
        role = Role.objects.get(name=role)
        role_folder = role.template_folder
    
    if module:
        return f'dashboard/{role_folder}/{module}/{base_template}'
    return f'dashboard/{role_folder}/{base_template}'

class FinanceManagementView(View):
    def get_template_name(self):
        return get_template_path('finance_dashboard.html', self.request.user.role, 'finance_management')

    def get(self, request):
        try:
            template_path = self.get_template_name()
            if not template_path:
                return HttpResponse("You do not have permission to view this page.", status=403)

            # Fetch all invoices, payments, expenses, TDS entries, financial years, and financial reports
            invoices = Invoice.objects.all()
            payments = Payment.objects.all()
            expenses = Expense.objects.all()
            tds_entries = TDSEntry.objects.all()
            financial_years = FinancialYear.objects.all()
            financial_reports = FinancialReport.objects.all()

            # Calculate statistics
            total_invoices = invoices.count()
            total_payments = payments.aggregate(total_amount=Sum('amount'))['total_amount'] or 0
            total_expenses = expenses.aggregate(total_amount=Sum('total_amount'))['total_amount'] or 0
            total_tds = tds_entries.aggregate(total_amount=Sum('tds_amount'))['total_amount'] or 0
            total_gst_collected = invoices.aggregate(total_gst=Sum('total_gst_amount'))['total_gst'] or 0
            net_profit = total_payments - total_expenses

            # Round values to 2 decimal places
            total_payments = round(total_payments, 2)
            total_expenses = round(total_expenses, 2)
            total_tds = round(total_tds, 2)
            total_gst_collected = round(total_gst_collected, 2)
            net_profit = round(net_profit, 2)

            # Pagination for invoices
            paginator = Paginator(invoices, 10)  # Show 10 invoices per page
            page = request.GET.get('page')
            try:
                invoices = paginator.page(page)
            except PageNotAnInteger:
                invoices = paginator.page(1)
            except EmptyPage:
                invoices = paginator.page(paginator.num_pages)

            # Context data to be passed to the template
            context = {
                'invoices': invoices,
                'payments': payments,
                'expenses': expenses,
                'tds_entries': tds_entries,
                'financial_years': financial_years,
                'financial_reports': financial_reports,
                'total_invoices': total_invoices,
                'total_payments': total_payments,
                'total_expenses': total_expenses,
                'total_tds': total_tds,
                'total_gst_collected': total_gst_collected,
                'net_profit': net_profit,
                'paginator': paginator,
                'page_obj': invoices,
                'user_role': request.user.role,  # Add user role to context
            }

            return render(request, template_path, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)