from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from .managers import UserManager

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('HRYUP_ADMIN', 'HRyUp Admin'),
        ('HRYUP_STAFF', 'HRyUp Staff'),
        ('CLIENT_MANAGER', 'Client Manager'),
        ('CLIENT_EMPLOYEE', 'Client Employee'),
    ]
    
    email = models.EmailField('email address', unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    privacy_consent = models.BooleanField(default=False)
    privacy_consent_date = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']
    
    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    @property
    def is_hryup_admin(self):
        return self.role == 'HRYUP_ADMIN'
    
    @property
    def is_hryup_staff(self):
        return self.role == 'HRYUP_STAFF'
    
    @property
    def is_client_manager(self):
        return self.role == 'CLIENT_MANAGER'
    
    @property
    def is_client_employee(self):
        return self.role == 'CLIENT_EMPLOYEE'
    
    @property
    def is_internal(self):
        return self.role in ('HRYUP_ADMIN', 'HRYUP_STAFF')
    
    def get_company(self):
        if self.is_hryup_admin:
            return None
        if self.is_hryup_staff:
            return None  # Staff can have multiple assigned companies
        if hasattr(self, 'employee_profile'):
            return self.employee_profile.company
        return None

class StaffAssignment(models.Model):
    """Tracks which HRyUp staff members are assigned to which client companies."""
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='staff_assignments',
        limit_choices_to={'role': 'HRYUP_STAFF'}
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='staff_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False, help_text='Primary staff contact for this company')
    
    class Meta:
        unique_together = ('staff', 'company')
        verbose_name = 'Staff Assignment'
        verbose_name_plural = 'Staff Assignments'
    
    def __str__(self):
        return f"{self.staff.get_full_name()} -> {self.company.name}"
