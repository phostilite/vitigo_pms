# Generated by Django 5.1.2 on 2025-01-15 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('RENT', 'Rent'), ('UTILITIES', 'Utilities'), ('SALARIES', 'Salaries'), ('SUPPLIES', 'Medical Supplies'), ('EQUIPMENT', 'Equipment'), ('MAINTENANCE', 'Maintenance'), ('MARKETING', 'Marketing'), ('OTHER', 'Other')], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('gst_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('date', models.DateField()),
                ('description', models.TextField()),
                ('vendor', models.CharField(max_length=255)),
                ('invoice_number', models.CharField(blank=True, max_length=50, null=True)),
                ('payment_method', models.CharField(choices=[('CASH', 'Cash'), ('UPI', 'UPI'), ('NEFT', 'NEFT'), ('CREDIT_CARD', 'Credit Card'), ('DEBIT_CARD', 'Debit Card'), ('CHEQUE', 'Cheque')], max_length=20)),
                ('receipt', models.FileField(blank=True, null=True, upload_to='expense_receipts/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='FinancialReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_type', models.CharField(choices=[('DAILY', 'Daily'), ('WEEKLY', 'Weekly'), ('MONTHLY', 'Monthly'), ('QUARTERLY', 'Quarterly'), ('YEARLY', 'Yearly'), ('CUSTOM', 'Custom')], max_length=20)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('total_revenue', models.DecimalField(decimal_places=2, max_digits=12)),
                ('total_expenses', models.DecimalField(decimal_places=2, max_digits=12)),
                ('net_profit', models.DecimalField(decimal_places=2, max_digits=12)),
                ('total_gst_collected', models.DecimalField(decimal_places=2, max_digits=12)),
                ('total_tds_deducted', models.DecimalField(decimal_places=2, max_digits=12)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('report_file', models.FileField(blank=True, null=True, upload_to='financial_reports/')),
            ],
        ),
        migrations.CreateModel(
            name='FinancialYear',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('is_current', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='GSTRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate', models.DecimalField(decimal_places=2, max_digits=5)),
                ('description', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_number', models.CharField(max_length=20, unique=True)),
                ('invoice_date', models.DateField()),
                ('due_date', models.DateField()),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('ISSUED', 'Issued'), ('PAID', 'Paid'), ('CANCELLED', 'Cancelled')], default='DRAFT', max_length=20)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('cgst_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('sgst_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('igst_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total_gst_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total_with_gst', models.DecimalField(decimal_places=2, max_digits=10)),
                ('notes', models.TextField(blank=True)),
                ('terms_and_conditions', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=255)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_date', models.DateTimeField()),
                ('payment_method', models.CharField(choices=[('CASH', 'Cash'), ('UPI', 'UPI'), ('NEFT', 'NEFT'), ('CREDIT_CARD', 'Credit Card'), ('DEBIT_CARD', 'Debit Card'), ('CHEQUE', 'Cheque')], max_length=20)),
                ('transaction_id', models.CharField(blank=True, max_length=100)),
                ('cheque_number', models.CharField(blank=True, max_length=50, null=True)),
                ('bank_name', models.CharField(blank=True, max_length=100, null=True)),
                ('upi_id', models.CharField(blank=True, max_length=50, null=True)),
                ('notes', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='TDSEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tds_rate', models.DecimalField(choices=[(0.1, '0.1%'), (1, '1%'), (2, '2%'), (5, '5%'), (10, '10%')], decimal_places=2, max_digits=4)),
                ('tds_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('date_deducted', models.DateField()),
            ],
        ),
    ]
