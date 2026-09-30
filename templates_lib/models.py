from django.db import models
from django.conf import settings
from core.models import TimeStampedModel

class HRTemplate(TimeStampedModel):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='hr_templates/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='uploaded_templates',
        limit_choices_to={'role__in': ['HRYUP_ADMIN', 'HRYUP_STAFF']}
    )

    def __str__(self):
        return self.title
