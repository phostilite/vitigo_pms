import pandas as pd
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from query_management.models import Query
import pytz
from datetime import datetime

class QueryVolumeReportGenerator:
    """Handles generation of Query Volume related reports"""
    
    @staticmethod
    def generate_temporal_query_count(start_date, end_date):
        """Generates Daily/Weekly/Monthly Query Count report"""
        
        # Get local timezone
        local_tz = timezone.get_current_timezone()
        
        # Get base queryset within date range
        queries = Query.objects.filter(
            created_at__range=(start_date, end_date)
        )

        # Create empty DataFrames with correct columns
        df_daily = pd.DataFrame(columns=['Date', 'Number of Queries'])
        df_weekly = pd.DataFrame(columns=['Week Starting', 'Number of Queries'])
        df_monthly = pd.DataFrame(columns=['Month', 'Number of Queries'])

        if queries.exists():
            # Daily counts
            daily_counts = list(queries.annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                count=Count('query_id')
            ).order_by('date'))

            # Weekly counts
            weekly_counts = list(queries.annotate(
                week=TruncWeek('created_at')
            ).values('week').annotate(
                count=Count('query_id')
            ).order_by('week'))

            # Monthly counts
            monthly_counts = list(queries.annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                count=Count('query_id')
            ).order_by('month'))

            # Convert timezone and create DataFrames
            if daily_counts:
                for entry in daily_counts:
                    # Convert date to datetime before timezone conversion
                    if isinstance(entry['date'], datetime):
                        entry['date'] = entry['date'].astimezone(local_tz).replace(tzinfo=None)
                    else:
                        # Convert date to datetime at midnight
                        entry['date'] = datetime.combine(entry['date'], datetime.min.time())
                df_daily = pd.DataFrame(daily_counts)
                df_daily.rename(columns={'date': 'Date', 'count': 'Number of Queries'}, inplace=True)

            if weekly_counts:
                for entry in weekly_counts:
                    if isinstance(entry['week'], datetime):
                        entry['week'] = entry['week'].astimezone(local_tz).replace(tzinfo=None)
                    else:
                        entry['week'] = datetime.combine(entry['week'], datetime.min.time())
                df_weekly = pd.DataFrame(weekly_counts)
                df_weekly.rename(columns={'week': 'Week Starting', 'count': 'Number of Queries'}, inplace=True)

            if monthly_counts:
                for entry in monthly_counts:
                    if isinstance(entry['month'], datetime):
                        entry['month'] = entry['month'].astimezone(local_tz).replace(tzinfo=None)
                    else:
                        entry['month'] = datetime.combine(entry['month'], datetime.min.time())
                df_monthly = pd.DataFrame(monthly_counts)
                df_monthly.rename(columns={'month': 'Month', 'count': 'Number of Queries'}, inplace=True)

        # Create unique filename using naive datetime
        temp_file = f'temp_report_{datetime.combine(start_date.date(), datetime.min.time()).strftime("%Y%m%d")}_{datetime.combine(end_date.date(), datetime.min.time()).strftime("%Y%m%d")}.xlsx'
        
        # Use context manager
        with pd.ExcelWriter(temp_file, engine='xlsxwriter') as excel_file:
            workbook = excel_file.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#0066cc',
                'font_color': 'white'
            })

            # Write sheets
            df_daily.to_excel(excel_file, sheet_name='Daily Counts', index=False)
            df_weekly.to_excel(excel_file, sheet_name='Weekly Counts', index=False)
            df_monthly.to_excel(excel_file, sheet_name='Monthly Counts', index=False)

            # Format headers and adjust column widths
            for sheet_name, df in [
                ('Daily Counts', df_daily),
                ('Weekly Counts', df_weekly),
                ('Monthly Counts', df_monthly)
            ]:
                worksheet = excel_file.sheets[sheet_name]
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    # Adjust column width based on content
                    if not df.empty:
                        max_length = max(
                            df[df.columns[col_num]].astype(str).apply(len).max(),
                            len(str(value))
                        )
                    else:
                        max_length = len(str(value))
                    worksheet.set_column(col_num, col_num, max_length + 2)

        return temp_file

class ReportGeneratorFactory:
    """Factory class to get appropriate report generator based on report type"""
    
    @staticmethod
    def get_generator(report_category, report_name):
        if report_category == "Query Volume Reports":
            if report_name == "Daily/Weekly/Monthly Query Count":
                return QueryVolumeReportGenerator.generate_temporal_query_count
        return None
