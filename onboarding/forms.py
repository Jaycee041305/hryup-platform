from django import forms
from .models import EmployeeOnboarding, OnboardingTemplate
from employees.models import Employee

class AssignOnboardingForm(forms.ModelForm):
    class Meta:
        model = EmployeeOnboarding
        fields = ['employee', 'template']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'template': forms.Select(attrs={'class': 'form-select'}),
        }
        
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['employee'].queryset = Employee.objects.filter(company=company, is_deleted=False)
            self.fields['template'].queryset = OnboardingTemplate.objects.filter(company=company, is_deleted=False)
