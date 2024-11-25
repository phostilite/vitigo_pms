import random
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandParser
from django.contrib.auth import get_user_model
from django.utils import timezone
from query_management.models import Query, QueryTag, QueryUpdate
from access_control.models import Role

class Command(BaseCommand):
    help = 'Populate the Query model with sample data'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            'num_queries',
            type=int,
            help='Number of queries to create'
        )
        # Make email optional with a default value
        parser.add_argument(
            '--email',
            type=str,
            help='Email of specific user to create queries for (optional)',
            required=False
        )

    def handle(self, *args, **kwargs):
        num_queries = kwargs['num_queries']

        # Get available staff members (users with staff roles)
        staff_roles = Role.objects.filter(name__in=['ADMIN', 'DOCTOR', 'NURSE', 'STAFF'])
        User = get_user_model()
        staff_users = User.objects.filter(role__in=staff_roles, is_active=True)
        
        if not staff_users.exists():
            self.stdout.write(self.style.ERROR('No staff users found. Please create staff users first.'))
            return

        # Sample data arrays
        subjects = [
            'Treatment inquiry', 'Appointment scheduling', 'Medicine consultation',
            'Follow-up request', 'Billing question', 'General inquiry',
            'Prescription refill', 'Side effects inquiry', 'Insurance coverage'
        ]
        
        descriptions = [
            'Need information about treatment options.',
            'Would like to schedule a follow-up appointment.',
            'Questions about prescribed medications.',
            'Requesting update on test results.',
            'Need clarification on recent billing.',
            'General questions about services.'
        ]

        sources = Query.SOURCE_CHOICES
        priorities = Query.PRIORITY_CHOICES
        statuses = Query.STATUS_CHOICES
        query_types = Query.QUERY_TYPE_CHOICES
        
        # Create sample tags
        tags = []
        for tag_name in ['Urgent', 'Follow-up', 'Billing', 'Treatment', 'Administrative', 'Technical']:
            tag, _ = QueryTag.objects.get_or_create(name=tag_name)
            tags.append(tag)

        queries_created = 0
        errors = 0

        for i in range(num_queries):
            try:
                # Randomly select users
                user = random.choice(staff_users)  # This will be the query creator
                assigned_to = random.choice(staff_users)  # This will be the assigned staff

                # Random dates within last 30 days
                created_at = timezone.now() - timedelta(days=random.randint(0, 30))
                
                # Create query
                query = Query.objects.create(
                    user=user,
                    assigned_to=assigned_to,
                    subject=random.choice(subjects),
                    description=random.choice(descriptions),
                    source=random.choice([s[0] for s in sources]),
                    priority=random.choice([p[0] for p in priorities]),
                    status=random.choice([s[0] for s in statuses]),
                    query_type=random.choice([t[0] for t in query_types]),
                    created_at=created_at,
                    is_anonymous=random.choice([True, False]),
                    contact_email=f"sample{i}@example.com" if random.choice([True, False]) else None,
                    contact_phone=f"+1234567890{i}" if random.choice([True, False]) else None,
                    is_patient=random.choice([True, False]),
                    conversion_status=random.choice([True, False]),
                    satisfaction_rating=random.choice([None, 1, 2, 3, 4, 5]),
                    expected_response_date=created_at + timedelta(days=random.randint(1, 5))
                )

                # Add random tags (1-3 tags per query)
                for tag in random.sample(tags, random.randint(1, 3)):
                    query.tags.add(tag)

                # Add sample updates
                num_updates = random.randint(0, 3)
                for j in range(num_updates):
                    update_time = created_at + timedelta(hours=random.randint(1, 24))
                    QueryUpdate.objects.create(
                        query=query,
                        user=random.choice(staff_users),
                        content=f"Sample update {j+1} for query {query.query_id}",
                        created_at=update_time
                    )

                # If status is resolved, add resolution date and summary
                if query.status == 'RESOLVED':
                    query.resolved_at = created_at + timedelta(days=random.randint(1, 3))
                    query.resolution_summary = "Issue has been resolved successfully."
                    query.response_time = query.resolved_at - created_at
                    query.save()

                queries_created += 1
                if queries_created % 10 == 0:
                    self.stdout.write(self.style.SUCCESS(f'Created {queries_created} queries...'))

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'Error creating query: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {queries_created} queries with {errors} errors'
        ))