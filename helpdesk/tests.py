from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import TenantModel
from companies.models import Company
from employees.models import Employee
from .models import Ticket, TicketReply, TicketEscalation

User = get_user_model()

class HelpdeskTests(TestCase):
    def setUp(self):
        # Create roles
        self.admin = User.objects.create_user(email='admin@hryup.com', password='pw', role='HRYUP_ADMIN', first_name='A', last_name='A')
        self.staff = User.objects.create_user(email='staff@hryup.com', password='pw', role='HRYUP_STAFF', first_name='S', last_name='S')
        
        self.company1 = Company.objects.create(name='Comp1')
        self.manager1 = User.objects.create_user(email='m1@comp1.com', password='pw', role='CLIENT_MANAGER', first_name='M', last_name='1')
        self.emp_profile1 = Employee.objects.create(user=self.manager1, company=self.company1, department='IT', position='Manager', hire_date='2020-01-01')
        
        self.employee1 = User.objects.create_user(email='e1@comp1.com', password='pw', role='CLIENT_EMPLOYEE', first_name='E', last_name='1')
        self.emp_profile_e1 = Employee.objects.create(user=self.employee1, company=self.company1, department='IT', position='Dev', hire_date='2020-01-01')

        self.company2 = Company.objects.create(name='Comp2')
        self.employee2 = User.objects.create_user(email='e2@comp2.com', password='pw', role='CLIENT_EMPLOYEE', first_name='E', last_name='2')
        self.emp_profile_e2 = Employee.objects.create(user=self.employee2, company=self.company2, department='HR', position='Dev', hire_date='2020-01-01')

    def test_ticket_creation_and_isolation(self):
        self.client.force_login(User.objects.get(email='e1@comp1.com'))
        response = self.client.post(reverse('helpdesk:ticket_submit'), {
            'category': 'IT',
            'subject': 'Laptop broken',
            'description': 'Needs fixing'
        })
        self.assertEqual(Ticket.objects.count(), 1)
        ticket = Ticket.objects.first()
        self.assertEqual(ticket.company, self.company1)
        self.assertEqual(ticket.employee, self.emp_profile_e1)
        
        # Test isolation
        self.client.force_login(User.objects.get(email='e2@comp2.com'))
        res = self.client.get(reverse('helpdesk:ticket_list'))
        self.assertNotIn(ticket, res.context['tickets'])
        
        # Manager can see
        self.client.force_login(User.objects.get(email='m1@comp1.com'))
        res = self.client.get(reverse('helpdesk:ticket_list'))
        self.assertIn(ticket, res.context['tickets'])

    def test_ticket_escalation(self):
        ticket = Ticket.objects.create(
            company=self.company1,
            employee=self.emp_profile_e1,
            category='IT',
            subject='Issue',
            description='Desc'
        )
        self.client.force_login(User.objects.get(email='staff@hryup.com'))
        res = self.client.post(reverse('helpdesk:ticket_escalate', args=[ticket.pk]), {
            'escalated_to': self.manager1.pk,
            'reason': 'Need manager approval'
        })
        self.assertEqual(TicketEscalation.objects.count(), 1)
        esc = TicketEscalation.objects.first()
        self.assertEqual(esc.escalated_to, self.manager1)
        self.assertEqual(esc.ticket, ticket)
