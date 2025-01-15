# Standard library imports
from datetime import datetime
import pytz

# Third-party imports
import pandas as pd

# Django imports
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone

# Local application imports
from query_management.models import Query
from .generators.query_volume_report_generator import QueryVolumeReportGenerator
from .generators.staff_report_generator import StaffReportGenerator
from .generators.performance_report_generator import PerformanceReportGenerator

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
        elif report_category == "Performance Reports":
            if report_name == "Average Response Time by Priority":
                return PerformanceReportGenerator.generate_response_time_by_priority
            elif report_name == "Resolution Time Analysis":
                return PerformanceReportGenerator.generate_resolution_time_analysis
            elif report_name == "Overdue Queries Report":
                return PerformanceReportGenerator.generate_overdue_queries_report
            elif report_name == "Pending Follow-ups List":
                return PerformanceReportGenerator.generate_pending_followups_list
            elif report_name == "User Satisfaction Ratings Summary":
                return PerformanceReportGenerator.generate_satisfaction_ratings_summary
        return None
