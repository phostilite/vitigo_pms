from django.apps import AppConfig


class ReportingAndAnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reporting_and_analytics'

    def ready(self):
        import reporting_and_analytics.signals
