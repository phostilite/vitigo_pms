from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.views import View
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from ..models import Document
from ..forms import DocumentUploadForm
from access_control.permissions import PermissionManager
from hr_management.utils import get_template_path
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging

logger = logging.getLogger(__name__)

class DocumentUploadView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('documents/upload_document.html', self.request.user.role, 'hr_management')

    def get(self, request):
        form = DocumentUploadForm()
        return render(request, self.get_template_name(), {'form': form})

    def post(self, request):
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                document = form.save(commit=False)
                document.uploaded_by = request.user
                
                if 'file' not in request.FILES:
                    messages.error(request, 'Please select a file to upload.')
                    return render(request, self.get_template_name(), {'form': form})
                
                document.save()
                messages.success(request, 'Document uploaded successfully!')
                return redirect('document_list')
            except Exception as e:
                messages.error(request, f'Error uploading document: {str(e)}')
                return render(request, self.get_template_name(), {'form': form})
        return render(request, self.get_template_name(), {'form': form})

class DocumentListView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('documents/document_list.html', self.request.user.role, 'hr_management')

    def get(self, request):
        try:
            # Get all documents first for total count
            all_documents = Document.objects.all()
            total_docs = all_documents.count()

            # Apply filters
            documents = all_documents.order_by('-uploaded_at')
            search_query = request.GET.get('search', '')
            document_type = request.GET.get('document_type', '')
            
            if search_query:
                documents = documents.filter(
                    Q(title__icontains=search_query) |
                    Q(description__icontains=search_query)
                )
            if document_type:
                documents = documents.filter(document_type=document_type)

            # Calculate other statistics
            document_types_count = Document.DOCUMENT_TYPES.__len__()
            recent_uploads_count = all_documents.filter(
                uploaded_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            expiring_count = all_documents.filter(
                expiry_date__isnull=False,
                expiry_date__lte=timezone.now() + timedelta(days=30)
            ).count()

            # Pagination
            page = request.GET.get('page', 1)
            paginator = Paginator(documents, 10)
            try:
                documents_page = paginator.page(page)
            except PageNotAnInteger:
                documents_page = paginator.page(1)
            except EmptyPage:
                documents_page = paginator.page(paginator.num_pages)

            # Check documents and mark those without files
            for doc in documents_page:
                try:
                    doc.file.url
                    doc.file_available = True
                except:
                    doc.file_available = False

            context = {
                'documents': documents_page,
                'total_documents': total_docs,  # Add total count separately
                'search_query': search_query,
                'document_type': document_type,
                'document_types': Document.DOCUMENT_TYPES,
                'document_types_count': document_types_count,
                'recent_uploads_count': recent_uploads_count,
                'expiring_count': expiring_count
            }
            return render(request, self.get_template_name(), context)
            
        except Exception as e:
            logger.error(f"Error loading documents: {str(e)}")
            messages.warning(request, "Some documents might be unavailable or corrupted")
            return render(request, self.get_template_name(), {
                'documents': [],
                'document_types': Document.DOCUMENT_TYPES,
                'total_documents': 0
            })
