from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordResetForm, SetPasswordForm
from .models import User

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autofocus': True,
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )

class UserRegistrationForm(UserCreationForm):
    company_name = forms.CharField(
        max_length=255, 
        required=True, 
        label="Company Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your business name'})
    )
    role = forms.ChoiceField(
        choices=[
            ('', '---------'),
            ('CLIENT_MANAGER', 'Client Manager'),
            ('CLIENT_EMPLOYEE', 'Client Employee'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'company_name', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            
            role = self.cleaned_data.get('role')
            company_name = self.cleaned_data.get('company_name')
            
            if company_name and role in ['CLIENT_MANAGER', 'CLIENT_EMPLOYEE']:
                from companies.models import Company
                from employees.models import Employee
                import datetime
                
                # Check if company exists by name (case-insensitive) to prevent duplicates if possible
                company = Company.objects.filter(name__iexact=company_name).first()
                if not company:
                    company = Company.objects.create(
                        name=company_name,
                        email=user.email,
                        phone=user.phone
                    )
                
                Employee.objects.create(
                    user=user,
                    company=company,
                    department='Management' if role == 'CLIENT_MANAGER' else 'General',
                    position='Manager' if role == 'CLIENT_MANAGER' else 'Employee',
                    hire_date=datetime.date.today(),
                    status=Employee.StatusChoices.ACTIVE
                )
        return user

class AdminUserCreateForm(forms.ModelForm):
    company = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select a company...",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'e.g. name_staff@hryup.ph'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from companies.models import Company
        self.fields['company'].queryset = Company.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        email = cleaned_data.get('email')
        company = cleaned_data.get('company')
        
        if role == 'HRYUP_STAFF' and email:
            if '_staff' not in email.split('@')[0]:
                self.add_error('email', 'Staff email username must contain "_staff" (e.g. name_staff@domain.com).')
                
        if role in ['CLIENT_MANAGER', 'CLIENT_EMPLOYEE'] and not company:
            self.add_error('company', 'A company is required for client roles.')
            
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        last_name = self.cleaned_data.get('last_name', 'User')
        role = self.cleaned_data.get('role')
        company = self.cleaned_data.get('company')
        
        # Generate password based on role
        if role == 'HRYUP_STAFF':
            password = f"{last_name.capitalize()}_staff"
        else:
            password = "password123!"
            
        user.set_password(password)
        if commit:
            user.save()
            
            # Create Employee profile if it's a client role
            if role in ['CLIENT_MANAGER', 'CLIENT_EMPLOYEE'] and company:
                from employees.models import Employee
                import datetime
                
                Employee.objects.create(
                    user=user,
                    company=company,
                    department='Management' if role == 'CLIENT_MANAGER' else 'General',
                    position='Manager' if role == 'CLIENT_MANAGER' else 'Employee',
                    hire_date=datetime.date.today(),
                    status=Employee.StatusChoices.ACTIVE
                )
                
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
