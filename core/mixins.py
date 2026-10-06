from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404

class RoleRequiredMixin(LoginRequiredMixin):
    required_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.required_roles and request.user.role not in self.required_roles:
            raise PermissionDenied("You do not have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)

class CompanyAccessMixin(LoginRequiredMixin):
    """Ensures user can only access their company's data."""
    
    def get_company(self):
        user = self.request.user
        
        # Helper to get company_id from any possible source
        company_id = (
            self.kwargs.get('company_id') or 
            self.request.GET.get('company') or 
            self.request.POST.get('company') or 
            self.request.session.get('active_company_id')
        )

        if user.role == 'HRYUP_ADMIN':
            if company_id:
                from companies.models import Company
                return Company.objects.filter(id=company_id).first()
            return None
            
        elif user.role == 'HRYUP_STAFF':
            if company_id:
                from companies.models import Company
                return Company.objects.filter(
                    id=company_id,
                    staff_assignments__staff=user
                ).first()
            return None
            
        else:
            if hasattr(user, 'employee_profile') and user.employee_profile:
                return user.employee_profile.company
                
        return None

class TenantQuerySetMixin:
    """Filters querysets by the current user's tenant."""
    
    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(qs, 'for_user'):
            return qs.for_user(self.request.user)
        return qs

class HRyUpAdminRequiredMixin(RoleRequiredMixin):
    required_roles = ['HRYUP_ADMIN']

class HRyUpStaffRequiredMixin(RoleRequiredMixin):
    required_roles = ['HRYUP_ADMIN', 'HRYUP_STAFF']

class ClientManagerRequiredMixin(RoleRequiredMixin):
    required_roles = ['HRYUP_ADMIN', 'HRYUP_STAFF', 'CLIENT_MANAGER']

class EmployeeSelfOnlyMixin(LoginRequiredMixin):
    """Ensures employees can only see their own records."""
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == 'CLIENT_EMPLOYEE':
            if hasattr(user, 'employee_profile'):
                if qs.model.__name__ == 'Employee':
                    return qs.filter(id=user.employee_profile.id)
                return qs.filter(employee=user.employee_profile)
            return qs.none()
        return qs
