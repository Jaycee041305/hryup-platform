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
            context['total_clients'] = Company.objects.count()
            context['active_subscriptions'] = Subscription.objects.filter(status='ACTIVE').count()
            context['open_tickets'] = Ticket.objects.filter(status='Open').count()
            
        elif user.role == 'CLIENT_MANAGER':
            if hasattr(user, 'employee_profile'):
                company = user.employee_profile.company
                context['headcount'] = Employee.objects.filter(company=company, status='ACTIVE').count()
                context['pending_leave'] = LeaveRequest.objects.filter(company=company, status='PENDING').count()
                context['open_vacancies'] = JobVacancy.objects.filter(company=company, status='Open').count()
                context['open_tickets'] = Ticket.objects.filter(company=company, status='Open').count()

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
            context['pending_leave'] = LeaveRequest.objects.filter(company_id__in=assigned_ids, status='PENDING').count()

        return context
