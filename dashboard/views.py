from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from companies.models import Company, Subscription
from employees.models import Employee
from attendance.models import Attendance
from leave.models import LeaveRequest, LeaveBalance
from recruitment.models import JobVacancy
from helpdesk.models import Ticket

class DashboardIndexView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard view serving data based on user roles.
    Template: dashboard/index.html
    """
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.role == 'HRYUP_ADMIN':
            from django.contrib.auth import get_user_model
            User = get_user_model()
            context['total_clients'] = Company.objects.count()
            context['active_clients'] = Company.objects.filter(is_active=True).count()
            context['open_tickets'] = Ticket.objects.filter(status='Open').count()
            context['staff_members'] = User.objects.filter(role='HRYUP_STAFF').prefetch_related('staff_assignments__company')
            context['recent_companies'] = Company.objects.order_by('-created_at')[:5]
            
        elif user.role == 'CLIENT_MANAGER':
            if hasattr(user, 'employee_profile'):
                company = user.employee_profile.company
                context['headcount'] = Employee.objects.filter(company=company, status='ACTIVE', is_deleted=False).count()
                context['pending_leave'] = LeaveRequest.objects.filter(company=company, status='PENDING', is_deleted=False).count()
                context['open_vacancies'] = JobVacancy.objects.filter(company=company, status='Open', is_deleted=False).count()
                context['open_tickets'] = Ticket.objects.filter(company=company, status='Open', is_deleted=False).count()
                context['recent_employees'] = Employee.objects.filter(company=company, status='ACTIVE', is_deleted=False).exclude(user__role='CLIENT_MANAGER').order_by('-created_at')[:5]
                context['recent_tickets'] = Ticket.objects.filter(company=company, is_deleted=False).order_by('-created_at')[:5]
                context['my_company'] = company

        elif user.role == 'CLIENT_EMPLOYEE':
            if hasattr(user, 'employee_profile'):
                emp = user.employee_profile
                context['leave_balances'] = LeaveBalance.objects.filter(employee=emp)
                context['recent_attendance'] = Attendance.objects.filter(employee=emp).order_by('-date')[:5]
                context['my_tickets'] = Ticket.objects.filter(employee=emp).order_by('-created_at')[:5]

        elif user.role == 'HRYUP_STAFF':
            context['assigned_companies'] = [a.company for a in user.staff_assignments.select_related('company')]
            assigned_ids = [c.id for c in context['assigned_companies']]
            context['open_tickets'] = Ticket.objects.filter(company_id__in=assigned_ids, status='Open').count()
            context['pending_clients'] = Company.objects.filter(is_active=True, staff_assignments__isnull=True).distinct().count()

        return context

from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

class ClientDashboardView(LoginRequiredMixin, TemplateView):
    """
    Operations Command Center for a specific client (used by Staff/Admin).
    Template: dashboard/client_dashboard.html
    """
    template_name = 'dashboard/client_dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['HRYUP_ADMIN', 'HRYUP_STAFF']:
            raise PermissionDenied("You do not have permission to view this client dashboard.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company_id = self.kwargs.get('company_id')
        company = get_object_or_404(Company, id=company_id)
        
        # Verify staff assignment if not admin
        if self.request.user.role == 'HRYUP_STAFF':
            if not self.request.user.staff_assignments.filter(company=company).exists():
                raise PermissionDenied("You are not assigned to this client.")
                
        context['client_company'] = company
        context['headcount'] = Employee.objects.filter(company=company, status='ACTIVE', is_deleted=False).count()
        context['pending_leave'] = LeaveRequest.objects.filter(company=company, status='PENDING', is_deleted=False).count()
        context['open_tickets'] = Ticket.objects.filter(company=company, status='Open', is_deleted=False).count()
        return context
