from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'description', 'object_type', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('description', 'user__email')
    
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]
        
    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False
