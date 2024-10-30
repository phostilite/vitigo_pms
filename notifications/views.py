# views.py

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.utils import timezone
from django.http import HttpResponse
from .models import UserNotification, SystemActivityLog, UserActivityLog, EmailNotification, SMSNotification, PushNotification
from django.db.models import Count

class NotificationManagementView(View):
    template_name = 'dashboard/admin/notifications/notification_dashboard.html'

    def get(self, request):
        try:
            # Fetch all notifications and logs
            user_notifications = UserNotification.objects.all()
            system_activity_logs = SystemActivityLog.objects.all()
            user_activity_logs = UserActivityLog.objects.all()
            email_notifications = EmailNotification.objects.all()
            sms_notifications = SMSNotification.objects.all()
            push_notifications = PushNotification.objects.all()

            # Calculate statistics
            total_user_notifications = user_notifications.count()
            total_system_activity_logs = system_activity_logs.count()
            total_user_activity_logs = user_activity_logs.count()
            total_email_notifications = email_notifications.count()
            total_sms_notifications = sms_notifications.count()
            total_push_notifications = push_notifications.count()

            # Pagination for user notifications
            paginator = Paginator(user_notifications, 10)  # Show 10 notifications per page
            page = request.GET.get('page')
            try:
                user_notifications = paginator.page(page)
            except PageNotAnInteger:
                user_notifications = paginator.page(1)
            except EmptyPage:
                user_notifications = paginator.page(paginator.num_pages)

            # Context data to be passed to the template
            context = {
                'user_notifications': user_notifications,
                'system_activity_logs': system_activity_logs,
                'user_activity_logs': user_activity_logs,
                'email_notifications': email_notifications,
                'sms_notifications': sms_notifications,
                'push_notifications': push_notifications,
                'total_user_notifications': total_user_notifications,
                'total_system_activity_logs': total_system_activity_logs,
                'total_user_activity_logs': total_user_activity_logs,
                'total_email_notifications': total_email_notifications,
                'total_sms_notifications': total_sms_notifications,
                'total_push_notifications': total_push_notifications,
                'paginator': paginator,
                'page_obj': user_notifications,
            }

            return render(request, self.template_name, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)