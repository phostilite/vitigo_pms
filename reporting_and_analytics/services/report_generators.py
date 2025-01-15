import pandas as pd
from django.db import models
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from query_management.models import Query
from django.contrib.auth import get_user_model
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

    @staticmethod
    def generate_source_distribution(start_date, end_date):
        """Generates Query Source Distribution report"""
        # Get base queryset within date range
        queries = Query.objects.filter(
            created_at__range=(start_date, end_date)
        )

        # Get source distribution
        source_counts = list(queries.values('source').annotate(
            count=Count('query_id')
        ).order_by('-count'))

        # Create DataFrame
        df = pd.DataFrame(source_counts)
        
        if not df.empty:
            # Map source codes to their display names
            source_mapping = dict(Query.SOURCE_CHOICES)
            df['source'] = df['source'].map(source_mapping)
            df.rename(columns={'source': 'Source', 'count': 'Number of Queries'}, inplace=True)

        # Create unique filename
        temp_file = f'temp_report_{datetime.combine(start_date.date(), datetime.min.time()).strftime("%Y%m%d")}_{datetime.combine(end_date.date(), datetime.min.time()).strftime("%Y%m%d")}.xlsx'
        
        # Write to Excel
        with pd.ExcelWriter(temp_file, engine='xlsxwriter') as excel_file:
            workbook = excel_file.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#0066cc',
                'font_color': 'white'
            })

            # Write sheet
            df.to_excel(excel_file, sheet_name='Source Distribution', index=False)

            # Format headers and adjust column widths
            worksheet = excel_file.sheets['Source Distribution']
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                if not df.empty:
                    max_length = max(
                        df[df.columns[col_num]].astype(str).apply(len).max(),
                        len(str(value))
                    )
                else:
                    max_length = len(str(value))
                worksheet.set_column(col_num, col_num, max_length + 2)

        return temp_file

    @staticmethod
    def generate_type_distribution(start_date, end_date):
        """Generates Query Type Distribution report"""
        # Get base queryset within date range
        queries = Query.objects.filter(
            created_at__range=(start_date, end_date)
        )

        # Get type distribution
        type_counts = list(queries.values('query_type').annotate(
            count=Count('query_id')
        ).order_by('-count'))

        # Create DataFrame
        df = pd.DataFrame(type_counts)
        
        if not df.empty:
            # Map type codes to their display names
            type_mapping = dict(Query.QUERY_TYPE_CHOICES)
            df['query_type'] = df['query_type'].map(type_mapping)
            df.rename(columns={'query_type': 'Query Type', 'count': 'Number of Queries'}, inplace=True)
            
            # Handle null/None values in query_type
            df['Query Type'].fillna('Unspecified', inplace=True)

        # Create unique filename
        temp_file = f'temp_report_{datetime.combine(start_date.date(), datetime.min.time()).strftime("%Y%m%d")}_{datetime.combine(end_date.date(), datetime.min.time()).strftime("%Y%m%d")}.xlsx'
        
        # Write to Excel
        with pd.ExcelWriter(temp_file, engine='xlsxwriter') as excel_file:
            workbook = excel_file.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#0066cc',
                'font_color': 'white'
            })

            # Write sheet
            df.to_excel(excel_file, sheet_name='Query Type Distribution', index=False)

            # Format headers and adjust column widths
            worksheet = excel_file.sheets['Query Type Distribution']
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                if not df.empty:
                    max_length = max(
                        df[df.columns[col_num]].astype(str).apply(len).max(),
                        len(str(value))
                    )
                else:
                    max_length = len(str(value))
                worksheet.set_column(col_num, col_num, max_length + 2)

        return temp_file

    @staticmethod
    def generate_user_type_distribution(start_date, end_date):
        """Generates Anonymous vs Registered User Query Distribution report"""
        # Get base queryset within date range
        queries = Query.objects.filter(
            created_at__range=(start_date, end_date)
        )

        # Get distribution by user type
        user_type_counts = list(queries.values('is_anonymous').annotate(
            count=Count('query_id')
        ).order_by('-count'))

        # Create DataFrame
        df = pd.DataFrame(user_type_counts)
        
        if not df.empty:
            # Map boolean values to readable labels
            df['is_anonymous'] = df['is_anonymous'].map({True: 'Anonymous', False: 'Registered User'})
            df.rename(columns={'is_anonymous': 'User Type', 'count': 'Number of Queries'}, inplace=True)

        # Create unique filename
        temp_file = f'temp_report_{datetime.combine(start_date.date(), datetime.min.time()).strftime("%Y%m%d")}_{datetime.combine(end_date.date(), datetime.min.time()).strftime("%Y%m%d")}.xlsx'
        
        # Write to Excel
        with pd.ExcelWriter(temp_file, engine='xlsxwriter') as excel_file:
            workbook = excel_file.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#0066cc',
                'font_color': 'white'
            })

            # Write sheet
            df.to_excel(excel_file, sheet_name='User Type Distribution', index=False)

            # Format headers and adjust column widths
            worksheet = excel_file.sheets['User Type Distribution']
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                if not df.empty:
                    max_length = max(
                        df[df.columns[col_num]].astype(str).apply(len).max(),
                        len(str(value))
                    )
                else:
                    max_length = len(str(value))
                worksheet.set_column(col_num, col_num, max_length + 2)

        return temp_file

class StaffReportGenerator:
    """Handles generation of Staff/Assignment related reports"""
    
    @staticmethod
    def generate_queries_per_staff(start_date, end_date):
        """Generates report showing distribution of queries among staff members"""
        User = get_user_model()
        
        # Get base queryset within date range
        queries = Query.objects.filter(
            created_at__range=(start_date, end_date),
            assigned_to__isnull=False
        )

        # Get distribution by staff member
        staff_counts = list(queries.values(
            'assigned_to',
            'assigned_to__first_name',
            'assigned_to__last_name',
            'assigned_to__email'
        ).annotate(
            count=Count('query_id'),
            resolved_count=Count('query_id', filter=models.Q(status='RESOLVED')),
            pending_count=Count('query_id', filter=~models.Q(status='RESOLVED'))
        ).order_by('-count'))

        # Create DataFrame
        df = pd.DataFrame(staff_counts)
        
        if not df.empty:
            # Create full name and format columns
            df['Staff Member'] = df['assigned_to__first_name'] + ' ' + df['assigned_to__last_name']
            df['Email'] = df['assigned_to__email']
            df.rename(columns={
                'count': 'Total Queries',
                'resolved_count': 'Resolved Queries',
                'pending_count': 'Pending Queries'
            }, inplace=True)
            
            # Select and order columns
            df = df[[
                'Staff Member',
                'Email',
                'Total Queries',
                'Resolved Queries',
                'Pending Queries'
            ]]

        # Create unique filename
        temp_file = f'temp_report_{datetime.combine(start_date.date(), datetime.min.time()).strftime("%Y%m%d")}_{datetime.combine(end_date.date(), datetime.min.time()).strftime("%Y%m%d")}.xlsx'
        
        # Write to Excel
        with pd.ExcelWriter(temp_file, engine='xlsxwriter') as excel_file:
            workbook = excel_file.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#0066cc',
                'font_color': 'white'
            })

            # Write sheet
            df.to_excel(excel_file, sheet_name='Queries per Staff', index=False)

            # Format headers and adjust column widths
            worksheet = excel_file.sheets['Queries per Staff']
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                if not df.empty:
                    max_length = max(
                        df[df.columns[col_num]].astype(str).apply(len).max(),
                        len(str(value))
                    )
                else:
                    max_length = len(str(value))
                worksheet.set_column(col_num, col_num, max_length + 2)

        return temp_file

    @staticmethod
    def generate_open_queries_by_staff(start_date, end_date):
        """Generates report showing current workload analysis by staff member"""
        User = get_user_model()
        
        # Get base queryset for open queries within date range
        queries = Query.objects.filter(
            created_at__range=(start_date, end_date),
            assigned_to__isnull=False
        ).exclude(status__in=['RESOLVED', 'CLOSED'])

        # Get workload distribution by staff member
        staff_workload = list(queries.values(
            'assigned_to',
            'assigned_to__first_name',
            'assigned_to__last_name',
            'assigned_to__email'
        ).annotate(
            total_open=Count('query_id'),
            high_priority=Count('query_id', filter=Q(priority='A')),
            medium_priority=Count('query_id', filter=Q(priority='B')),
            low_priority=Count('query_id', filter=Q(priority='C')),
            waiting_response=Count('query_id', filter=Q(status='WAITING')),
            in_progress=Count('query_id', filter=Q(status='IN_PROGRESS')),
            new_queries=Count('query_id', filter=Q(status='NEW'))
        ).order_by('-total_open'))

        # Create DataFrame
        df = pd.DataFrame(staff_workload)
        
        if not df.empty:
            # Create full name and format columns
            df['Staff Member'] = df['assigned_to__first_name'] + ' ' + df['assigned_to__last_name']
            df['Email'] = df['assigned_to__email']
            
            # Select and order columns
            df = df[[
                'Staff Member',
                'Email',
                'total_open',
                'high_priority',
                'medium_priority',
                'low_priority',
                'new_queries',
                'in_progress',
                'waiting_response'
            ]]
            
            # Rename columns for better readability
            df.rename(columns={
                'total_open': 'Total Open Queries',
                'high_priority': 'High Priority',
                'medium_priority': 'Medium Priority',
                'low_priority': 'Low Priority',
                'new_queries': 'New',
                'in_progress': 'In Progress',
                'waiting_response': 'Waiting for Response'
            }, inplace=True)

        # Create unique filename
        temp_file = f'temp_report_{datetime.combine(start_date.date(), datetime.min.time()).strftime("%Y%m%d")}_{datetime.combine(end_date.date(), datetime.min.time()).strftime("%Y%m%d")}.xlsx'
        
        # Write to Excel
        with pd.ExcelWriter(temp_file, engine='xlsxwriter') as excel_file:
            workbook = excel_file.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#0066cc',
                'font_color': 'white'
            })

            # Write sheet
            df.to_excel(excel_file, sheet_name='Open Queries by Staff', index=False)

            # Format headers and adjust column widths
            worksheet = excel_file.sheets['Open Queries by Staff']
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                if not df.empty:
                    max_length = max(
                        df[df.columns[col_num]].astype(str).apply(len).max(),
                        len(str(value))
                    )
                else:
                    max_length = len(str(value))
                worksheet.set_column(col_num, col_num, max_length + 2)

        return temp_file

    @staticmethod
    def generate_unassigned_queries_list(start_date, end_date):
        """Generates report showing queries that are pending assignment"""
        # Get base queryset for unassigned queries within date range
        queries = Query.objects.filter(
            created_at__range=(start_date, end_date),
            assigned_to__isnull=True
        ).values(
            'query_id',
            'subject',
            'created_at',
            'source',
            'priority',
            'query_type',
            'status'
        ).order_by('-created_at')

        # Create DataFrame
        df = pd.DataFrame(list(queries))
        
        if not df.empty:
            # Map codes to their display names
            source_mapping = dict(Query.SOURCE_CHOICES)
            priority_mapping = dict(Query.PRIORITY_CHOICES)
            type_mapping = dict(Query.QUERY_TYPE_CHOICES)
            status_mapping = dict(Query.STATUS_CHOICES)

            # Apply mappings and rename columns
            df['source'] = df['source'].map(source_mapping)
            df['priority'] = df['priority'].map(priority_mapping)
            df['query_type'] = df['query_type'].map(type_mapping)
            df['status'] = df['status'].map(status_mapping)
            
            # Handle null values in query_type
            df['query_type'].fillna('Unspecified', inplace=True)
            
            # Rename columns for better readability
            df.rename(columns={
                'query_id': 'Query ID',
                'subject': 'Subject',
                'created_at': 'Created Date',
                'source': 'Source',
                'priority': 'Priority',
                'query_type': 'Query Type',
                'status': 'Status'
            }, inplace=True)

            # Reorder columns
            df = df[[
                'Query ID',
                'Subject',
                'Created Date',
                'Priority',
                'Query Type',
                'Source',
                'Status'
            ]]

        # Create unique filename
        temp_file = f'temp_report_{datetime.combine(start_date.date(), datetime.min.time()).strftime("%Y%m%d")}_{datetime.combine(end_date.date(), datetime.min.time()).strftime("%Y%m%d")}.xlsx'
        
        # Write to Excel
        with pd.ExcelWriter(temp_file, engine='xlsxwriter') as excel_file:
            workbook = excel_file.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#0066cc',
                'font_color': 'white'
            })

            # Write sheet
            df.to_excel(excel_file, sheet_name='Unassigned Queries', index=False)

            # Format headers and adjust column widths
            worksheet = excel_file.sheets['Unassigned Queries']
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                if not df.empty:
                    max_length = max(
                        df[df.columns[col_num]].astype(str).apply(len).max(),
                        len(str(value))
                    )
                else:
                    max_length = len(str(value))
                worksheet.set_column(col_num, col_num, max_length + 2)

        return temp_file

    @staticmethod
    def generate_staff_performance_metrics(start_date, end_date):
        """Generates comprehensive staff performance analysis report"""
        User = get_user_model()
        
        # Get base queryset for the date range
        queries = Query.objects.filter(
            created_at__range=(start_date, end_date),
            assigned_to__isnull=False
        )

        # Get detailed performance metrics by staff member
        staff_metrics = list(queries.values(
            'assigned_to',
            'assigned_to__first_name',
            'assigned_to__last_name',
            'assigned_to__email'
        ).annotate(
            total_queries=Count('query_id'),
            resolved_queries=Count('query_id', filter=Q(status='RESOLVED')),
            # Resolution rate
            resolution_rate=Count('query_id', filter=Q(status='RESOLVED')) * 100.0 / Count('query_id'),
            # Average response time for resolved queries
            avg_response_time=models.Avg('response_time', filter=Q(status='RESOLVED')),
            # High priority handling
            high_priority_total=Count('query_id', filter=Q(priority='A')),
            high_priority_resolved=Count('query_id', filter=Q(priority='A', status='RESOLVED')),
            # Satisfaction metrics
            avg_satisfaction=models.Avg('satisfaction_rating', filter=Q(satisfaction_rating__isnull=False)),
            rated_queries=Count('query_id', filter=Q(satisfaction_rating__isnull=False)),
            # Conversion metrics
            conversion_count=Count('query_id', filter=Q(conversion_status=True)),
            convertible_queries=Count('query_id', filter=Q(conversion_status__isnull=False))
        ).order_by('-total_queries'))

        # Create DataFrame
        df = pd.DataFrame(staff_metrics)
        
        if not df.empty:
            # Create full name and format columns
            df['Staff Member'] = df['assigned_to__first_name'] + ' ' + df['assigned_to__last_name']
            df['Email'] = df['assigned_to__email']
            
            # Calculate additional metrics
            df['Resolution Rate (%)'] = df['resolution_rate'].round(2)
            df['High Priority Resolution Rate (%)'] = (
                df['high_priority_resolved'] * 100.0 / df['high_priority_total']
            ).round(2).fillna(0)
            df['Conversion Rate (%)'] = (
                df['conversion_count'] * 100.0 / df['convertible_queries']
            ).round(2).fillna(0)
            
            # Format average response time
            df['Average Response Time'] = df['avg_response_time'].apply(
                lambda x: str(x).split('.')[0] if pd.notnull(x) else 'N/A'
            )
            
            # Select and order columns
            df = df[[
                'Staff Member',
                'Email',
                'total_queries',
                'resolved_queries',
                'Resolution Rate (%)',
                'Average Response Time',
                'high_priority_total',
                'high_priority_resolved',
                'High Priority Resolution Rate (%)',
                'avg_satisfaction',
                'rated_queries',
                'Conversion Rate (%)'
            ]]
            
            # Rename columns for better readability
            df.rename(columns={
                'total_queries': 'Total Queries',
                'resolved_queries': 'Resolved Queries',
                'high_priority_total': 'High Priority Queries',
                'high_priority_resolved': 'High Priority Resolved',
                'avg_satisfaction': 'Average Satisfaction (1-5)',
                'rated_queries': 'Number of Rated Queries'
            }, inplace=True)

        # Create unique filename
        temp_file = f'temp_report_{datetime.combine(start_date.date(), datetime.min.time()).strftime("%Y%m%d")}_{datetime.combine(end_date.date(), datetime.min.time()).strftime("%Y%m%d")}.xlsx'
        
        # Write to Excel
        with pd.ExcelWriter(temp_file, engine='xlsxwriter') as excel_file:
            workbook = excel_file.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#0066cc',
                'font_color': 'white'
            })

            # Write sheet
            df.to_excel(excel_file, sheet_name='Staff Performance Metrics', index=False)

            # Format headers and adjust column widths
            worksheet = excel_file.sheets['Staff Performance Metrics']
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
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
            elif report_name == "Queries by Source":
                return QueryVolumeReportGenerator.generate_source_distribution
            elif report_name == "Queries by Type":
                return QueryVolumeReportGenerator.generate_type_distribution
            elif report_name == "Anonymous vs Registered User Queries":
                return QueryVolumeReportGenerator.generate_user_type_distribution
        elif report_category == "Staff/Assignment Reports":
            if report_name == "Queries per Staff Member":
                return StaffReportGenerator.generate_queries_per_staff
            elif report_name == "Open Queries by Assigned Staff":
                return StaffReportGenerator.generate_open_queries_by_staff
            elif report_name == "Unassigned Queries List":
                return StaffReportGenerator.generate_unassigned_queries_list
            elif report_name == "Staff Performance Metrics":
                return StaffReportGenerator.generate_staff_performance_metrics
        return None
