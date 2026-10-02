from django.db import models
from core.models import TimeStampedModel, SoftDeleteModel
import uuid

class Company(TimeStampedModel, SoftDeleteModel):
    name = models.CharField(max_length=255)
    attendance_qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    trade_name = models.CharField(max_length=255, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    tin = models.CharField('TIN', max_length=50, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100, default='Las Piñas City')
    province = models.CharField(max_length=100, default='Metro Manila')
    zip_code = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(
        max_length=20,
        choices=[
            ('MICRO', 'Micro (1-9)'),
            ('SMALL', 'Small (10-99)'),
            ('MEDIUM', 'Medium (100-199)'),
        ],
        default='MICRO'
    )
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    objects = models.Manager()
    
    class Meta:
        verbose_name_plural = 'companies'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def active_subscription(self):
        return self.subscriptions.filter(status='ACTIVE').first()
    
    @property
    def employee_count(self):
        return self.employees_employee_set.filter(is_deleted=False, status='ACTIVE').count()
    
    def has_module(self, module_name):
        sub = self.active_subscription
        if sub and sub.package:
            return getattr(sub.package, f'module_{module_name}', False)
        return False


class SubscriptionPackage(TimeStampedModel):
    TIER_CHOICES = [
        ('BASIC', 'Basic'),
        ('STANDARD', 'Standard'),
        ('PREMIUM', 'Premium'),
    ]
    
    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    description = models.TextField(blank=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_annually = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_employees = models.PositiveIntegerField(default=10)
    
    # Module toggles
    module_recruitment = models.BooleanField(default=False)
    module_onboarding = models.BooleanField(default=False)
    module_employee_records = models.BooleanField(default=True)
    module_attendance = models.BooleanField(default=False)
    module_leave = models.BooleanField(default=False)
    module_payroll = models.BooleanField(default=False)
    module_helpdesk = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['price_monthly']
    
    def __str__(self):
        return f"{self.name} ({self.tier})"


class Subscription(TimeStampedModel):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('SUSPENDED', 'Suspended'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='subscriptions')
    package = models.ForeignKey(SubscriptionPackage, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    start_date = models.DateField()
    expiry_date = models.DateField()
    billing_cycle = models.CharField(
        max_length=10,
        choices=[('MONTHLY', 'Monthly'), ('ANNUALLY', 'Annually')],
        default='MONTHLY'
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.company.name} - {self.package.name} ({self.status})"
    
    @property
    def is_active(self):
        from django.utils import timezone
        return self.status == 'ACTIVE' and self.expiry_date >= timezone.now().date()
