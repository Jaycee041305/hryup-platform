from django import forms
from django.contrib.auth import authenticate
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

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(
                self.request, username=username, password=password
            )
            if self.user_cache is None:
                # Check if account exists with valid password but is inactive (pending onboarding approval)
                user = User.objects.filter(email__iexact=username).first()
                if user and user.check_password(password) and not user.is_active:
                    if user.role == 'CLIENT_EMPLOYEE':
                        raise forms.ValidationError(
                            "Your account is pending onboarding approval by your company manager/HR. "
                            "You will be able to log in once your application has been approved.",
                            code="pending_approval",
                        )
                    else:
                        raise forms.ValidationError(
                            "This account is currently inactive. Please contact your system administrator.",
                            code="inactive",
                        )
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

class UserRegistrationForm(UserCreationForm):
    company = forms.ModelChoiceField(
        queryset=None,
        required=True,
        label="Company",
        empty_label="Select your company...",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    position = forms.CharField(
        max_length=100,
        required=False,
        label="Job Title / Position",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Sales Associate, Accountant (optional)'})
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'company', 'position']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from companies.models import Company
        self.fields['company'].queryset = Company.objects.filter(is_deleted=False).order_by('name')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Public sign-up is strictly for Client Employees awaiting onboarding approval
        user.role = 'CLIENT_EMPLOYEE'
        user.is_active = False
        if commit:
            user.save()
            
            company = self.cleaned_data.get('company')
            position = self.cleaned_data.get('position') or 'Employee'
            
            if company:
                from employees.models import Employee
                from onboarding.models import OnboardingTemplate, OnboardingTask, EmployeeOnboarding, EmployeeOnboardingTask
                import datetime
                
                employee = Employee.objects.create(
                    user=user,
                    company=company,
                    department='General',
                    position=position,
                    hire_date=datetime.date.today(),
                    status=Employee.StatusChoices.PENDING_APPROVAL
                )
                
                # Ensure default onboarding template exists for company
                template = OnboardingTemplate.objects.filter(company=company).first()
                if not template:
                    template = OnboardingTemplate.objects.create(
                        title='Standard New Hire Checklist',
                        company=company
                    )
                    default_tasks = [
                        'Submit Government IDs (SSS, PhilHealth, Pag-IBIG, TIN)',
                        'Sign Non-Disclosure Agreement (NDA)',
                        'Read and Acknowledge Employee Handbook',
                        'Setup Company Email and IT Accounts',
                        'Attend HR Orientation'
                    ]
                    for desc in default_tasks:
                        OnboardingTask.objects.create(template=template, description=desc, company=company)
                
                tracker = EmployeeOnboarding.objects.create(
                    employee=employee,
                    template=template,
                    company=company,
                    status='pending'
                )
                
                # Create checklist tasks for the employee
                tasks_to_create = [
                    EmployeeOnboardingTask(
                        onboarding=tracker,
                        task=t,
                        company=company
                    )
                    for t in template.tasks.all()
                ]
                if tasks_to_create:
                    EmployeeOnboardingTask.objects.bulk_create(tasks_to_create)
                    
        return user

class AdminUserCreateForm(forms.ModelForm):
    company = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select a company...",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    custom_password = forms.CharField(
        required=False,
        label="Custom Password (Optional)",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to use default password'}),
        help_text="Leave blank to use default password (password123! or LastName_staff)."
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'role', 'company', 'custom_password']
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
        self.fields['company'].queryset = Company.objects.filter(is_deleted=False)

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        email = cleaned_data.get('email')
        company = cleaned_data.get('company')
        
        if role == 'HRYUP_STAFF' and email:
            if '_staff' not in email.split('@')[0]:
                self.add_error('email', 'Staff email username must contain "_staff" (e.g. name_staff@domain.com).')
                
        if role in ['CLIENT_MANAGER', 'CLIENT_EMPLOYEE'] and not company:
            self.add_error('company', 'A company is required for Client Manager and Client Employee accounts.')
            
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        last_name = self.cleaned_data.get('last_name', 'User')
        role = self.cleaned_data.get('role')
        company = self.cleaned_data.get('company')
        custom_password = self.cleaned_data.get('custom_password')
        
        # Determine password
        if custom_password:
            password = custom_password
        elif role == 'HRYUP_STAFF':
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
