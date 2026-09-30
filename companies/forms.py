from django import forms
from .models import Company, SubscriptionPackage, Subscription

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'trade_name': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'tin': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'company_size': forms.Select(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SubscriptionPackageForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPackage
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tier': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price_monthly': forms.NumberInput(attrs={'class': 'form-control'}),
            'price_annually': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_employees': forms.NumberInput(attrs={'class': 'form-control'}),
            'module_recruitment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'module_onboarding': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'module_employee_records': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'module_attendance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'module_leave': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'module_payroll': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'module_helpdesk': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['package', 'status', 'start_date', 'expiry_date', 'billing_cycle', 'notes']
        widgets = {
            'package': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'billing_cycle': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
