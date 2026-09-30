from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

def role_required(*roles):
    """Decorator that checks if the user has one of the specified roles."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied("You do not have permission to access this page.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def company_access_required(view_func):
    """Decorator that ensures the user has access to the company in the request."""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        company_id = kwargs.get('company_id')
        if not company_id:
            raise PermissionDenied("Company not specified.")
        
        user = request.user
        if user.role == 'HRYUP_ADMIN':
            return view_func(request, *args, **kwargs)
        elif user.role == 'HRYUP_STAFF':
            if not user.staff_assignments.filter(company_id=company_id).exists():
                raise PermissionDenied("You are not assigned to this company.")
        elif user.role in ('CLIENT_MANAGER', 'CLIENT_EMPLOYEE'):
            if not hasattr(user, 'employee_profile') or str(user.employee_profile.company_id) != str(company_id):
                raise PermissionDenied("You do not belong to this company.")
        else:
            raise PermissionDenied()
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view
