def get_client_ip(request):
    """Extract client IP from request, handling proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def log_action(user=None, action='', description='', obj=None, request=None, extra_data=None):
    """Create an audit log entry."""
    from .models import AuditLog
    
    entry = AuditLog(
        user=user,
        action=action,
        description=description,
        extra_data=extra_data,
    )
    
    if obj:
        entry.object_type = obj.__class__.__name__
        entry.object_id = str(obj.pk)
        entry.object_repr = str(obj)[:255]
    
    if request:
        entry.ip_address = get_client_ip(request)
        entry.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    
    entry.save()
    return entry
