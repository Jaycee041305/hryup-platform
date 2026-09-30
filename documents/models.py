from django.db import models
from django.conf import settings
from core.models import TenantModel
from employees.models import Employee

class Document201(TenantModel):
    class CategoryChoices(models.TextChoices):
        RESUME = 'RESUME', 'Resume'
        CONTRACT = 'CONTRACT', 'Contract'
        ID = 'ID', 'ID'
        MEDICAL = 'MEDICAL', 'Medical'
        OTHER = 'OTHER', 'Other'

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    category = models.CharField(max_length=20, choices=CategoryChoices.choices)
    file = models.FileField(upload_to='201_files/')
    confidentiality_flag = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')

    def __str__(self):
        return f"{self.category} - {self.employee}"
