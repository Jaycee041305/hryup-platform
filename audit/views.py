from django.views.generic import ListView
from core.mixins import HRyUpAdminRequiredMixin as AdminRequiredMixin
from .models import AuditLog

class AuditLogListView(AdminRequiredMixin, ListView):
    """
    HRyUp Admin only.
    Template: audit/audit_log_list.html
    Context: logs (paginated by 50), filterable by action, user, date range.
    """
    model = AuditLog
    template_name = 'audit/audit_log_list.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        action = self.request.GET.get('action')
        user = self.request.GET.get('user')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if action:
            queryset = queryset.filter(action=action)
        if user:
            queryset = queryset.filter(user__email__icontains=user)
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
            
        return queryset
