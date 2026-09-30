from django.db import models
from core.models import TenantModel
from employees.models import Employee

class PayrollPeriod(TenantModel):
    class StatusChoices(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        LOCKED = 'LOCKED', 'Locked'

    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.OPEN)

    def __str__(self):
        return f"{self.start_date} to {self.end_date} - {self.get_status_display()}"

    class Meta:
        ordering = ['-start_date']

class PayrollEntry(TenantModel):
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='entries')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payroll_entries')
    
    total_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    late_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    absent_days = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    approved_leave_days = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    basic_rate = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    allowances = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    net_compiled_pay = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.employee} - {self.period}"
    
    class Meta:
        unique_together = ('period', 'employee')
        verbose_name_plural = 'Payroll entries'
