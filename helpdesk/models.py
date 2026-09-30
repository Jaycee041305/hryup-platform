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
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='tickets')
    category = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Open')
    assigned_staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', limit_choices_to={'role': 'HRYUP_STAFF'})

    def __str__(self):
        return f"{self.subject} ({self.get_status_display()})"

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
