from django.db import models

class TenantQuerySet(models.QuerySet):
    def for_company(self, company):
        return self.filter(company=company)
    
    def for_user(self, user):
        """Filter based on user's role and company."""
        if hasattr(user, 'role'):
            if user.role in ('HRYUP_ADMIN',):
                return self
            elif user.role == 'HRYUP_STAFF':
                assigned_company_ids = user.staff_assignments.values_list('company_id', flat=True)
                return self.filter(company_id__in=assigned_company_ids)
            elif user.role in ('CLIENT_MANAGER', 'CLIENT_EMPLOYEE'):
                if hasattr(user, 'employee_profile') and user.employee_profile:
                    return self.filter(company=user.employee_profile.company)
        return self.none()

class TenantManager(models.Manager):
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db).filter(is_deleted=False)
    
    def for_company(self, company):
        return self.get_queryset().for_company(company)
    
    def for_user(self, user):
        return self.get_queryset().for_user(user)
