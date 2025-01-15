import pandas as pd
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from query_management.models import Query

class QueryVolumeReportGenerator:
    """Handles generation of Query Volume related reports"""
    
    @staticmethod
    def generate_temporal_query_count(start_date, end_date):
        """Generates Daily/Weekly/Monthly Query Count report"""
        
        # Get base queryset within date range
        queries = Query.objects.filter(
            created_at__range=(start_date, end_date)
        )

        # Daily counts
        daily_counts = queries.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        # Weekly counts
        weekly_counts = queries.annotate(
            week=TruncWeek('created_at')
        ).values('week').annotate(
            count=Count('id')
        ).order_by('week')

        # Monthly counts
        monthly_counts = queries.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

        # Create DataFrames
        df_daily = pd.DataFrame(daily_counts)
        df_weekly = pd.DataFrame(weekly_counts)
        df_monthly = pd.DataFrame(monthly_counts)

        # Create Excel writer object
        excel_file = pd.ExcelWriter('temp_report.xlsx', engine='xlsxwriter')

        # Write each DataFrame to a different worksheet
        df_daily.to_excel(excel_file, sheet_name='Daily Counts', index=False)
        df_weekly.to_excel(excel_file, sheet_name='Weekly Counts', index=False)
        df_monthly.to_excel(excel_file, sheet_name='Monthly Counts', index=False)

        # Save the Excel file
        excel_file.save()

        return 'temp_report.xlsx'

class ReportGeneratorFactory:
    """Factory class to get appropriate report generator based on report type"""
    
    @staticmethod
    def get_generator(report_category, report_name):
        if report_category == "Query Volume Reports":
            if report_name == "Daily/Weekly/Monthly Query Count":
                return QueryVolumeReportGenerator.generate_temporal_query_count
        return None
