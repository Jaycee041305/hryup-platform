from django.db import models
from core.models import TenantModel
from employees.models import Employee

class OnboardingTemplate(TenantModel):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title

class OnboardingTask(TenantModel):
    template = models.ForeignKey(OnboardingTemplate, on_delete=models.CASCADE, related_name='tasks')
    description = models.TextField()

    def __str__(self):
        return f"Task for {self.template.title}"

class EmployeeOnboarding(TenantModel):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='onboardings')
    template = models.ForeignKey(OnboardingTemplate, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.template.title}"

class EmployeeOnboardingTask(TenantModel):
    onboarding = models.ForeignKey(EmployeeOnboarding, on_delete=models.CASCADE, related_name='employee_tasks')
    task = models.ForeignKey(OnboardingTask, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.task.description} - {'Done' if self.is_completed else 'Pending'}"

class PolicyDocument(TenantModel):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='onboarding/policies/')

    def __str__(self):
        return self.title

class PolicyAcknowledgment(TenantModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='acknowledgments')
    document = models.ForeignKey(PolicyDocument, on_delete=models.CASCADE)
    signed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.user.get_full_name()} signed {self.document.title}"
