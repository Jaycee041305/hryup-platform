from django.db import models
from core.models import TenantModel
from django.core.exceptions import ValidationError
from django.db.models import Q

class LeaveType(TenantModel):
    name = models.CharField(max_length=100)
    default_days = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return self.name

class LeaveBalance(TenantModel):
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    remaining_days = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    class Meta:
        unique_together = ('employee', 'leave_type')

    def __str__(self):
        return f"{self.employee} - {self.leave_type.name}: {self.remaining_days}"

class LeaveRequest(TenantModel):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)

    def __str__(self):
        return f"{self.employee} ({self.leave_type.name}) {self.start_date} to {self.end_date}"

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    def clean(self):
        super().clean()
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError("Start date cannot be after end date.")
            
            # Overlap validation
            overlapping = LeaveRequest.objects.filter(
                employee=self.employee,
                status__in=[self.StatusChoices.PENDING, self.StatusChoices.APPROVED],
                is_deleted=False
            ).exclude(pk=self.pk).filter(
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            )
            if overlapping.exists():
                raise ValidationError("Leave dates overlap with an existing request.")
            
            # Balance validation (only if it's new or still pending and being updated)
            if self.status == self.StatusChoices.PENDING:
                try:
                    balance = LeaveBalance.objects.get(employee=self.employee, leave_type=self.leave_type, is_deleted=False)
                    if self.duration_days > balance.remaining_days:
                        raise ValidationError("Requested days exceed remaining leave balance.")
                except LeaveBalance.DoesNotExist:
                    raise ValidationError("No leave balance found for this leave type.")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            old_status = LeaveRequest.objects.get(pk=self.pk).status

        super().save(*args, **kwargs)

        # Automatic balance deduction
        if old_status != self.StatusChoices.APPROVED and self.status == self.StatusChoices.APPROVED:
            try:
                balance = LeaveBalance.objects.get(employee=self.employee, leave_type=self.leave_type, is_deleted=False)
                balance.remaining_days -= self.duration_days
                balance.save()
            except LeaveBalance.DoesNotExist:
                pass
