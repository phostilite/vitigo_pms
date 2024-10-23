import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from query_management.models import Query, QueryTag

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate the Query model with sample data for a user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the user to populate queries for')
        parser.add_argument('num_queries', type=int, help='Number of queries to create')

    def handle(self, *args, **kwargs):
        email = kwargs['email']
        num_queries = kwargs['num_queries']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email "{email}" does not exist'))
            return

        sources = ['WEBSITE', 'CHATBOT', 'SOCIAL_MEDIA', 'PHONE', 'IVR', 'EMAIL', 'WALK_IN', 'MOBILE_APP']
        priorities = ['A', 'B', 'C']
        statuses = ['NEW', 'IN_PROGRESS', 'WAITING', 'RESOLVED', 'CLOSED']

        for _ in range(num_queries):
            query = Query.objects.create(
                patient=user,
                subject=f'Sample Query {_ + 1}',
                description=f'This is a sample description for query {_ + 1}.',
                source=random.choice(sources),
                priority=random.choice(priorities),
                status=random.choice(statuses),
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            query.tags.add(QueryTag.objects.get_or_create(name=f'SampleTag{_ + 1}')[0])
            self.stdout.write(self.style.SUCCESS(f'Created query with ID {query.query_id}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully created {num_queries} queries for user with email "{email}"'))