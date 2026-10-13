from django import forms
from .models import Company, SubscriptionPackage, Subscription

class CompanyForm(forms.ModelForm):
    # Optional Client Manager creation during company onboarding
    manager_first_name = forms.CharField(
        max_length=150,
        required=False,
        label="Manager First Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. John'})
    )
    manager_last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Manager Last Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Doe'})
    )
    manager_email = forms.EmailField(
        required=False,
        label="Manager Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'e.g. manager@clientcompany.com'})
    )
    manager_phone = forms.CharField(
        max_length=20,
        required=False,
        label="Manager Phone",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 09123456789'})
    )
    manager_password = forms.CharField(
        max_length=128,
        required=False,
        label="Manager Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank for default (password123!)'}),
        help_text="Leave blank to use default password (password123!)."
    )

    class Meta:
        model = Company
        fields = [
            'name', 'trade_name', 'registration_number', 'tin', 'address',
            'city', 'province', 'zip_code', 'phone', 'email', 'website',
            'industry', 'company_size', 'logo', 'is_active',
            'manager_first_name', 'manager_last_name', 'manager_email',
            'manager_phone', 'manager_password'
        ]
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'city' in self.fields:
            self.fields['city'].required = False
            self.fields['city'].initial = 'Las Piñas City'
        if 'province' in self.fields:
            self.fields['province'].required = False
            self.fields['province'].initial = 'Metro Manila'
        if 'company_size' in self.fields:
            self.fields['company_size'].required = False
            self.fields['company_size'].initial = 'MICRO'

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('city'):
            cleaned_data['city'] = 'Las Piñas City'
        if not cleaned_data.get('province'):
            cleaned_data['province'] = 'Metro Manila'
        if not cleaned_data.get('company_size'):
            cleaned_data['company_size'] = 'MICRO'

        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        m_email = cleaned_data.get('manager_email')
        m_first = cleaned_data.get('manager_first_name')
        m_last = cleaned_data.get('manager_last_name')
        
        # If any manager field is provided, require first name, last name, and email
        if m_email or m_first or m_last:
            if not m_first:
                self.add_error('manager_first_name', 'Manager first name is required when creating a manager account.')
            if not m_last:
                self.add_error('manager_last_name', 'Manager last name is required when creating a manager account.')
            if not m_email:
                self.add_error('manager_email', 'Manager email is required when creating a manager account.')
            elif User.objects.filter(email=m_email).exists():
                self.add_error('manager_email', 'A user with this email address already exists.')
                
        return cleaned_data


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

from accounts.models import StaffAssignment

class StaffAssignmentForm(forms.ModelForm):
    class Meta:
        model = StaffAssignment
        fields = ['staff', 'is_primary']
        widgets = {
            'staff': forms.Select(attrs={'class': 'form-select'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

