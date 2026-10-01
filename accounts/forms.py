from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordResetForm, SetPasswordForm
from .models import User

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

class UserRegistrationForm(UserCreationForm):
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
        fields = ['email', 'first_name', 'last_name', 'phone', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AdminUserCreateForm(forms.ModelForm):
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

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        email = cleaned_data.get('email')
        
        if role == 'HRYUP_STAFF' and email:
            if '_staff' not in email.split('@')[0]:
                self.add_error('email', 'Staff email username must contain "_staff" (e.g. name_staff@domain.com).')
                
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        first_name = self.cleaned_data.get('first_name', 'User')
        # Generate password based on first name
        password = f"{first_name.capitalize()}123!"
        user.set_password(password)
        if commit:
            user.save()
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
