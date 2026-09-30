from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.contrib import messages
from .models import HRTemplate
from .forms import HRTemplateForm
import os

@login_required
def template_list(request):
    templates = HRTemplate.objects.all().order_by('-created_at')
    
    if request.user.is_hryup_admin or request.user.is_hryup_staff:
        if request.method == 'POST':
            form = HRTemplateForm(request.POST, request.FILES)
            if form.is_valid():
                new_template = form.save(commit=False)
                new_template.uploaded_by = request.user
                new_template.save()
                messages.success(request, "Template uploaded successfully.")
                return redirect('templates_lib:template_list')
        else:
            form = HRTemplateForm()
    else:
        form = None

    return render(request, 'templates_lib/template_list.html', {
        'templates': templates,
        'form': form
    })

@login_required
def template_download(request, pk):
    template = get_object_or_404(HRTemplate, pk=pk)
    
    # Check file exists
    if not template.file or not os.path.exists(template.file.path):
        raise Http404("File not found")
        
    response = FileResponse(open(template.file.path, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(template.file.name)}"'
    return response
