from django.db import models
from core.models import TenantModel

class JobVacancy(TenantModel):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('draft', 'Draft'),
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

class Application(TenantModel):
    STATUS_CHOICES = (
        ('new', 'New'),
        ('screened', 'Screened'),
        ('shortlisted', 'Shortlisted'),
        ('interview', 'Interview'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    )
    vacancy = models.ForeignKey(JobVacancy, on_delete=models.CASCADE, related_name='applications')
    applicant_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    cv_file = models.FileField(upload_to='recruitment/cvs/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    privacy_consent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.applicant_name} - {self.vacancy.title}"

class ScreeningNote(TenantModel):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='notes')
    note = models.TextField()
    added_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Note on {self.application.applicant_name} by {self.added_by}"
