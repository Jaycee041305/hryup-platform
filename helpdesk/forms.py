from django import forms
from .models import Ticket, TicketReply, TicketEscalation

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['category', 'subject', 'description']
        widgets = {
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class TicketReplyForm(forms.ModelForm):
    class Meta:
        model = TicketReply
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Type your reply...'}),
        }

class TicketStatusForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'})
        }

class TicketEscalationForm(forms.ModelForm):
    class Meta:
        model = TicketEscalation
        fields = ['escalated_to', 'reason']
        widgets = {
            'escalated_to': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            # Users who are CLIENT_MANAGER in the ticket's company
            self.fields['escalated_to'].queryset = User.objects.filter(role='CLIENT_MANAGER', employee_profile__company=company)
