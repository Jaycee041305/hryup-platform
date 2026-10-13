from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.views.generic import TemplateView, UpdateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from .models import User
from .forms import EmailAuthenticationForm, UserUpdateForm, CustomPasswordResetForm, CustomSetPasswordForm, UserRegistrationForm, AdminUserCreateForm

class CustomLoginView(LoginView):
    """
    Template name: accounts/login.html
    Context variables: form
    """
    authentication_form = EmailAuthenticationForm
    template_name = 'accounts/login.html'
    
    def form_valid(self, form):
        remember_me = self.request.POST.get('remember_me')
        if not remember_me:
            # Session expires when browser closes
            self.request.session.set_expiry(0)
        else:
            # Session expires in 30 days
            self.request.session.set_expiry(30 * 24 * 60 * 60)
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse_lazy('dashboard:index')

class CustomLogoutView(LogoutView):
    """
    Template name: None
    Context variables: None
    """
    next_page = reverse_lazy('core:landing')

class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Template name: accounts/profile.html
    Context variables: user, form
    """
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UserUpdateForm(instance=self.request.user)
        return context

class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Template name: accounts/profile_edit.html
    Context variables: form
    """
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    success_message = "Profile updated successfully."
    
    def get_object(self, queryset=None):
        return self.request.user

class CustomPasswordResetView(PasswordResetView):
    """
    Template name: accounts/password_reset.html
    Context variables: form
    """
    form_class = CustomPasswordResetForm
    template_name = 'accounts/password_reset.html'
    success_url = reverse_lazy('accounts:password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    """
    Template name: accounts/password_reset_done.html
    """
    template_name = 'accounts/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Template name: accounts/password_reset_confirm.html
    Context variables: form, validlink
    """
    form_class = CustomSetPasswordForm
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """
    Template name: accounts/password_reset_complete.html
    """
    template_name = 'accounts/password_reset_complete.html'

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Template name: accounts/user_list.html
    Context variables: object_list (users paginated), page_obj
    """
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.role == 'HRYUP_ADMIN'

    def get_queryset(self):
        from django.db.models import Q
        qs = User.objects.all().order_by('-date_joined')
        query = self.request.GET.get('q')
        role = self.request.GET.get('role')
        if query:
            qs = qs.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            )
        if role:
            qs = qs.filter(role=role)
        return qs

class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    """
    Template name: accounts/user_create.html
    Context variables: form
    """
    model = User
    form_class = AdminUserCreateForm
    template_name = 'accounts/user_create.html'
    success_message = "User account created successfully!"
    
    def test_func(self):
        return self.request.user.role == 'HRYUP_ADMIN'

    def get_initial(self):
        initial = super().get_initial()
        role = self.request.GET.get('role')
        company_id = self.request.GET.get('company')
        if role:
            initial['role'] = role
        if company_id:
            initial['company'] = company_id
        return initial

    def get_success_url(self):
        company_id = self.request.GET.get('company') or (self.object.company.pk if self.object.company else None)
        if company_id and self.object.role == 'CLIENT_MANAGER':
            return reverse_lazy('companies:detail', kwargs={'pk': company_id})
        return reverse_lazy('accounts:user_list')

class PublicSignUpView(CreateView):
    """
    Public sign up page exclusively for Client Employees.
    Template name: accounts/signup.html
    """
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, "Employee account created successfully! Please log in.")
        return super().form_valid(form)

