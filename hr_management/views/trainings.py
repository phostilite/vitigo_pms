# Standard library imports
import logging

# Django imports
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db import models
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View

# Local imports
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler500
from hr_management.models import Training
from hr_management.utils import get_template_path

class TrainingListView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('trainings/training_list.html', self.request.user.role, 'hr_management')

    def get(self, request):
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        date_filter = request.GET.get('date_filter', '')

        trainings = Training.objects.prefetch_related('participants').all()
        today = timezone.now().date()

        # Apply filters
        if search_query:
            trainings = trainings.filter(
                Q(title__icontains=search_query) |
                Q(trainer__icontains=search_query)
            )

        if status_filter:
            trainings = trainings.filter(status=status_filter)

        if date_filter:
            if date_filter == 'upcoming':
                trainings = trainings.filter(start_date__gt=today)
            elif date_filter == 'ongoing':
                trainings = trainings.filter(start_date__lte=today, end_date__gte=today)
            elif date_filter == 'past':
                trainings = trainings.filter(end_date__lt=today)

        # Ordering
        trainings = trainings.order_by('-start_date')

        # Pagination
        paginator = Paginator(trainings, 10)
        page = request.GET.get('page', 1)
        try:
            trainings_page = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            trainings_page = paginator.page(1)

        context = {
            'trainings': trainings_page,
            'search_query': search_query,
            'status_filter': status_filter,
            'date_filter': date_filter,
        }

        return render(request, self.get_template_name(), context)