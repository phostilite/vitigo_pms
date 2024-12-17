from datetime import timedelta
from django.db.models import Avg, Count, Sum, F, ExpressionWrapper, DurationField
from django.utils import timezone
from clinic_management.models import ClinicVisit, ClinicStation, VisitPaymentTransaction, StaffAssignment
import logging
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()

def get_quick_stats(today):
        try:
            # Calculate average wait time using start_time - registration_time
            completed_visits = ClinicVisit.objects.filter(
                registration_time__date=today,
                start_time__isnull=False
            ).annotate(
                wait_duration=ExpressionWrapper(
                    F('start_time') - F('registration_time'),
                    output_field=DurationField()
                )
            )
            
            avg_wait_minutes = completed_visits.aggregate(
                avg_wait=Avg('wait_duration')
            )['avg_wait']

            # Convert timedelta to minutes if not None
            avg_wait_time = round(avg_wait_minutes.total_seconds() / 60) if avg_wait_minutes else 0
            
            # Get current queue count (active_queue)
            active_queue = ClinicVisit.objects.filter(
                status='WAITING'
            ).count()

            # Get high priority cases count
            high_priority = ClinicVisit.objects.filter(
                status='WAITING',
                priority='A'  # Assuming 'A' is high priority
            ).count()
            
            # Calculate completion rate based on daily target
            completed_visits_count = ClinicVisit.objects.filter(
                status='COMPLETED',
                end_time__date=today
            ).count()
            
            # Assuming a daily target of 50 visits - you may want to make this configurable
            DAILY_TARGET = 50
            completion_rate = round((completed_visits_count / DAILY_TARGET) * 100) if DAILY_TARGET > 0 else 0
            # Cap the rate at 100%
            completion_rate = min(completion_rate, 100)
            
            # Calculate resource utilization stats
            stations = ClinicStation.objects.filter(is_active=True)
            
            # Count all treatment rooms (including consultation and exam rooms)
            total_rooms = stations.count()
            
            # Count occupied treatment rooms
            occupied_rooms = stations.filter(
                current_status='OCCUPIED'
            ).count()

            # Calculate overall resource utilization percentage
            resource_utilization = round((occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0)
            
            # Calculate available rooms
            available_rooms = total_rooms - occupied_rooms

            # Calculate today's revenue and comparison with last week
            today_transactions = VisitPaymentTransaction.objects.filter(
                processed_at__date=today,
                status='COMPLETED'
            )
            
            today_revenue = today_transactions.aggregate(
                total=Sum('amount')
            )['total'] or 0

            # Calculate last week's revenue for the same weekday
            last_week = today - timedelta(days=7)
            last_week_revenue = VisitPaymentTransaction.objects.filter(
                processed_at__date=last_week,
                status='COMPLETED'
            ).aggregate(
                total=Sum('amount')
            )['total'] or 0

            # Calculate revenue growth percentage
            revenue_growth = 0
            if last_week_revenue > 0:
                revenue_growth = round(((today_revenue - last_week_revenue) / last_week_revenue) * 100, 1)

            # Get staff assignments for today
            staff_assignments = StaffAssignment.objects.filter(
                date=today,
                status__in=['SCHEDULED', 'IN_PROGRESS']
            ).select_related('staff')

            # Get unique staff members on duty
            staff_on_duty = staff_assignments.values('staff').distinct().count()
            
            # Get total active staff
            total_staff = User.objects.filter(
                is_active=True,
                role__name__in=['DOCTOR', 'NURSE', 'STAFF']
            ).count()

            # Count staff by role
            doctors_on_duty = staff_assignments.filter(
                staff__role__name='DOCTOR'
            ).values('staff').distinct().count()

            nurses_on_duty = staff_assignments.filter(
                staff__role__name='NURSE'
            ).values('staff').distinct().count()

            other_staff_on_duty = staff_assignments.filter(
                staff__role__name='STAFF'
            ).values('staff').distinct().count()

            # Get appointment statistics for today
            now = timezone.now()
            today_appointments = ClinicVisit.objects.filter(
                appointment__date=today
            ).select_related('appointment', 'appointment__time_slot')
            
            total_appointments = today_appointments.count()
            
            # Get upcoming appointments - using time_slot's start_time
            upcoming_appointments = today_appointments.filter(
                status__in=['REGISTERED', 'WAITING'],
                appointment__time_slot__start_time__gte=now.time()  # Compare with current time
            ).order_by('appointment__time_slot__start_time')
            
            upcoming_count = upcoming_appointments.count()
            
            # Get next appointment time
            next_appointment = upcoming_appointments.first()
            next_appointment_time = (
                next_appointment.appointment.time_slot.start_time.strftime('%H:%M')
                if next_appointment and next_appointment.appointment and next_appointment.appointment.time_slot
                else 'None'
            )

            return {
                'total_patients_today': ClinicVisit.objects.filter(
                    registration_time__date=today
                ).count(),
                'active_visits': ClinicVisit.objects.filter(
                    status__in=['REGISTERED', 'WAITING', 'IN_PROGRESS']
                ).count(),
                'completed_visits': completed_visits_count,
                'completion_rate': completion_rate,
                'avg_wait_time': avg_wait_time,
                'active_queue': active_queue,
                'high_priority': high_priority,
                'resource_utilization': resource_utilization,
                'available_rooms': available_rooms,
                'total_rooms': total_rooms,
                'today_revenue': today_revenue,
                'revenue_growth': revenue_growth,
                'last_week_revenue': last_week_revenue,
                'staff_on_duty': staff_on_duty,
                'total_staff': total_staff,
                'doctors_on_duty': doctors_on_duty,
                'nurses_on_duty': nurses_on_duty,
                'other_staff_on_duty': other_staff_on_duty,
                'total_appointments': total_appointments,
                'upcoming_count': upcoming_count,
                'next_appointment_time': next_appointment_time
            }
        except Exception as e:
            logger.error(f"Error getting quick stats: {str(e)}")
            return {}