# help_support/views.py

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.utils import timezone
from django.http import HttpResponse
from .models import SupportTicket, SupportResponse, FAQ, KnowledgeBaseArticle, SupportCategory, SupportRating
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

class HelpSupportManagementView(View):
    def get_template_name(self):
        return get_template_path('help_support_dashboard.html', self.request.user.role, 'help_support')

    def get(self, request):
        try:
            template_path = self.get_template_name()
            
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)

            # Fetch all help and support data
            support_tickets = SupportTicket.objects.all()
            support_responses = SupportResponse.objects.all()
            faqs = FAQ.objects.all()
            knowledge_base_articles = KnowledgeBaseArticle.objects.all()
            support_categories = SupportCategory.objects.all()
            support_ratings = SupportRating.objects.all()

            # Calculate statistics
            total_tickets = support_tickets.count()
            total_responses = support_responses.count()
            total_faqs = faqs.count()
            total_articles = knowledge_base_articles.count()
            total_categories = support_categories.count()
            total_ratings = support_ratings.count()

            # Pagination for support tickets
            paginator = Paginator(support_tickets, 10)  # Show 10 tickets per page
            page = request.GET.get('page')
            try:
                support_tickets = paginator.page(page)
            except PageNotAnInteger:
                support_tickets = paginator.page(1)
            except EmptyPage:
                support_tickets = paginator.page(paginator.num_pages)

            # Context data to be passed to the template
            context = {
                'support_tickets': support_tickets,
                'support_responses': support_responses,
                'faqs': faqs,
                'knowledge_base_articles': knowledge_base_articles,
                'support_categories': support_categories,
                'support_ratings': support_ratings,
                'total_tickets': total_tickets,
                'total_responses': total_responses,
                'total_faqs': total_faqs,
                'total_articles': total_articles,
                'total_categories': total_categories,
                'total_ratings': total_ratings,
                'paginator': paginator,
                'page_obj': support_tickets,
                'user_role': request.user.role,  # Add user role to context
            }

            return render(request, template_path, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)