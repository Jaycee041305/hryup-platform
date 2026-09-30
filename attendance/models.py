from django.db import models
from core.models import TenantModel

class WorkSchedule(TenantModel):
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='schedules')
    days_of_week = models.CharField(max_length=50, help_text="e.g. Mon,Tue,Wed,Thu,Fri")
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.employee} ({self.start_time} - {self.end_time})"

class Attendance(TenantModel):
    class ReviewStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    is_manual_entry = models.BooleanField(default=False)
    review_status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)

    def __str__(self):
        return f"{self.employee} on {self.date}"
