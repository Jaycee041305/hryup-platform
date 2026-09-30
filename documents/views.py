from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from django.http import FileResponse, Http404
from core.mixins import CompanyAccessMixin, TenantQuerySetMixin, EmployeeSelfOnlyMixin
from .models import Document201
from django.conf import settings

class DocumentListView(CompanyAccessMixin, EmployeeSelfOnlyMixin, TenantQuerySetMixin, ListView):
    model = Document201
    template_name = 'documents/document_list.html'
    context_object_name = 'documents'

class DocumentCreateView(CompanyAccessMixin, TenantQuerySetMixin, CreateView):
    model = Document201
    template_name = 'documents/document_form.html'
    fields = ['employee', 'category', 'file', 'confidentiality_flag']
    success_url = reverse_lazy('documents:list')

    def form_valid(self, form):
        file = form.cleaned_data.get('file')
        if file:
            max_size = getattr(settings, 'FILE_UPLOAD_MAX_SIZE', 10 * 1024 * 1024)
            if file.size > max_size:
                form.add_error('file', 'File size must be under 10MB.')
                return self.form_invalid(form)
            
            allowed_types = getattr(settings, 'ALLOWED_FILE_TYPES', ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'xlsx', 'xls', 'csv'])
            ext = file.name.split('.')[-1].lower()
            if ext not in allowed_types:
                form.add_error('file', 'Unsupported file extension.')
                return self.form_invalid(form)
                
        form.instance.company = self.get_company()
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)

class DocumentDownloadView(CompanyAccessMixin, EmployeeSelfOnlyMixin, TenantQuerySetMixin, DetailView):
    model = Document201
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.file:
            return FileResponse(self.object.file.open('rb'), as_attachment=True, filename=self.object.file.name.split('/')[-1])
        raise Http404("File not found")
