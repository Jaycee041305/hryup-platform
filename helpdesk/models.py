from django.db import models
from django.conf import settings
from core.models import TenantModel

class Ticket(TenantModel):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Waiting on Client', 'Waiting on Client'),
        ('Resolved', 'Resolved'),
    ]
    employee = models.ForeignKey('employees.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_tickets')
    category = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Open')
    assigned_staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', limit_choices_to={'role': 'HRYUP_STAFF'})

    def __str__(self):
        return f"{self.subject} ({self.get_status_display()})"

    @property
    def submitter_name(self):
        if self.employee and hasattr(self.employee, 'user') and self.employee.user:
            return self.employee.user.get_full_name()
        if self.created_by:
            return self.created_by.get_full_name()
        return "Anonymous Submitter"

    @property
    def submitter_email(self):
        if self.employee and hasattr(self.employee, 'user') and self.employee.user:
            return self.employee.user.email
        if self.created_by:
            return self.created_by.email
        return ""

class TicketReply(TenantModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='replies')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()

    def __str__(self):
        return f"Reply by {self.sender.get_full_name()} on {self.ticket.subject}"

class TicketEscalation(TenantModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='escalations')
    escalated_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'CLIENT_MANAGER'})
    reason = models.TextField()

    def __str__(self):
        return f"Escalated {self.ticket.subject} to {self.escalated_to.get_full_name()}"
