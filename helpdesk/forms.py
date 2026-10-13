from django import forms
from .models import Ticket, TicketReply, TicketEscalation

from companies.models import Company

class TicketForm(forms.ModelForm):
    CATEGORY_CHOICES = [
        ('General HR Inquiry', 'General HR Inquiry'),
        ('Payroll & Compensation', 'Payroll & Compensation'),
        ('Attendance & Time Logs', 'Attendance & Time Logs'),
        ('Leave Request & Balances', 'Leave Request & Balances'),
        ('201 File & Employment Records', '201 File & Employment Records'),
        ('IT', 'IT / Technical Support'),
        ('Company Policy & Guidelines', 'Company Policy & Guidelines'),
        ('Account & Login Assistance', 'Account & Login Assistance'),
        ('Other', 'Other'),
    ]

    company = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_deleted=False).order_by('name'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Client Company",
        empty_label="Select client company..."
    )
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        initial='General HR Inquiry',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Category"
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Brief summary of your inquiry (e.g. Missing Time Out log on Monday)'
        }),
        label="Subject / Summary"
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Please provide complete details about your inquiry, issue, or request...'
        }),
        label="Detailed Description"
    )

    class Meta:
        model = Ticket
        fields = ['category', 'subject', 'description']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and (user.is_hryup_admin or user.is_hryup_staff):
            self.fields['company'].required = True
            # Reorder fields so company is first
            field_order = ['company', 'category', 'subject', 'description']
            self.order_fields(field_order)
        else:
            self.fields.pop('company', None)

class TicketReplyForm(forms.ModelForm):
    class Meta:
        model = TicketReply
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Type your reply here...'
            }),
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
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for escalating to manager...'}),
        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            # Users who are CLIENT_MANAGER in the ticket's company
            self.fields['escalated_to'].queryset = User.objects.filter(role='CLIENT_MANAGER', employee_profile__company=company)
