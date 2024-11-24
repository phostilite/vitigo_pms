# views.py

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.utils import timezone
from django.http import HttpResponse
from .models import UserNotification, SystemActivityLog, UserActivityLog, EmailNotification, SMSNotification, PushNotification
from django.db.models import Count
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

class NotificationManagementView(View):
    def get_template_name(self):
        return get_template_path('notification_dashboard.html', self.request.user.role, 'notifications')

    def get(self, request):
        try:
            # Get user role from request
            user_role = request.user.role  # Assuming role is stored in user model

            # Get template path
            template_path = self.get_template_name()
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)

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
                'user_role': user_role,  # Add user role to context
            }

            return render(request, template_path, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)