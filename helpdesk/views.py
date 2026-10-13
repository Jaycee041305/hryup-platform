from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
import datetime

from companies.models import Company
from employees.models import Employee
from .models import Ticket, TicketReply, TicketEscalation
from .forms import TicketForm, TicketReplyForm, TicketStatusForm, TicketEscalationForm

@login_required
def ticket_list(request):
    user = request.user
    if user.is_hryup_admin:
        # Admin can see all tickets across all client companies
        tickets_qs = Ticket.objects.all().select_related('company', 'employee__user', 'assigned_staff', 'created_by')
    elif user.is_hryup_staff:
        # Staff can see all tickets or tickets assigned to them / unassigned
        assigned_companies = user.staff_assignments.values_list('company_id', flat=True)
        if assigned_companies.exists():
            tickets_qs = Ticket.objects.filter(
                Q(assigned_staff=user) | Q(company_id__in=assigned_companies) | Q(assigned_staff__isnull=True)
            ).select_related('company', 'employee__user', 'assigned_staff', 'created_by')
        else:
            tickets_qs = Ticket.objects.all().select_related('company', 'employee__user', 'assigned_staff', 'created_by')
    elif user.is_client_manager:
        company = user.get_company()
        if not company and hasattr(user, 'employee_profile') and user.employee_profile:
            company = user.employee_profile.company
        if company:
            tickets_qs = Ticket.objects.filter(company=company).select_related('company', 'employee__user', 'assigned_staff', 'created_by')
        else:
            tickets_qs = Ticket.objects.none()
    else:
        # Client employee
        employee = getattr(user, 'employee_profile', None)
        if employee:
            tickets_qs = Ticket.objects.filter(
                Q(employee=employee) | Q(created_by=user)
            ).select_related('company', 'employee__user', 'assigned_staff', 'created_by')
        else:
            tickets_qs = Ticket.objects.filter(created_by=user).select_related('company', 'employee__user', 'assigned_staff', 'created_by')

    # Metrics calculation before filtering
    total_count = tickets_qs.count()
    open_count = tickets_qs.filter(status='Open').count()
    in_progress_count = tickets_qs.filter(status='In Progress').count()
    waiting_count = tickets_qs.filter(status='Waiting on Client').count()
    resolved_count = tickets_qs.filter(status='Resolved').count()

    # Apply status filter if present
    status_filter = request.GET.get('status')
    if status_filter:
        tickets = tickets_qs.filter(status=status_filter).order_by('-created_at')
    else:
        tickets = tickets_qs.order_by('-created_at')

    context = {
        'tickets': tickets,
        'status_filter': status_filter,
        'total_count': total_count,
        'open_count': open_count,
        'in_progress_count': in_progress_count,
        'waiting_count': waiting_count,
        'resolved_count': resolved_count,
    }
    return render(request, 'helpdesk/ticket_list.html', context)

@login_required
def ticket_submit(request):
    user = request.user
    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or 
        request.content_type == 'application/json' or 
        request.POST.get('is_ajax') == 'true'
    )
    
    # Resolve company for client roles
    user_company = user.get_company()
    if not user_company and hasattr(user, 'employee_profile') and user.employee_profile:
        user_company = user.employee_profile.company

    if request.method == 'POST':
        form = TicketForm(request.POST, user=user)
        if form.is_valid():
            ticket = form.save(commit=False)
            
            # Determine company
            if user.is_hryup_admin or user.is_hryup_staff:
                selected_company = form.cleaned_data.get('company')
                if selected_company:
                    ticket.company = selected_company
                elif user_company:
                    ticket.company = user_company
                else:
                    ticket.company = Company.objects.filter(is_deleted=False).first()
            else:
                ticket.company = user_company

            if not ticket.company:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Unable to determine your company.'}, status=400)
                messages.error(request, "Unable to determine your company. Please contact support.")
                return render(request, 'helpdesk/ticket_form.html', {'form': form, 'user_company': user_company})

            # Determine employee profile
            employee = getattr(user, 'employee_profile', None)
            if not employee and user.role in ['CLIENT_EMPLOYEE', 'CLIENT_MANAGER'] and ticket.company:
                employee = Employee.objects.filter(user=user, company=ticket.company).first()
                if not employee:
                    employee = Employee.objects.create(
                        user=user,
                        company=ticket.company,
                        department='General' if user.role == 'CLIENT_EMPLOYEE' else 'Management',
                        position='Employee' if user.role == 'CLIENT_EMPLOYEE' else 'Manager',
                        hire_date=datetime.date.today(),
                        status=Employee.StatusChoices.ACTIVE
                    )

            ticket.employee = employee
            ticket.created_by = user
            ticket.status = 'Open'
            ticket.save()

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'ticket_id': ticket.pk,
                    'ticket_url': reverse('helpdesk:ticket_detail', kwargs={'pk': ticket.pk}),
                    'subject': ticket.subject,
                    'category': ticket.category,
                    'message': f"Ticket #{ticket.id} submitted successfully! Our HR team will review your inquiry shortly."
                })

            messages.success(request, f"Ticket #{ticket.id} submitted successfully! Your HR team will review your inquiry shortly.")
            return redirect('helpdesk:ticket_detail', pk=ticket.pk)
        else:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            messages.error(request, "Please check the form for errors.")
    else:
        form = TicketForm(user=user)

    return render(request, 'helpdesk/ticket_form.html', {
        'form': form,
        'user_company': user_company,
    })

@login_required
def ticket_detail(request, pk):
    user = request.user
    
    # Queryset with access control
    if user.is_hryup_admin or user.is_hryup_staff:
        qs = Ticket.objects.all()
    elif user.is_client_manager:
        company = user.get_company()
        if not company and hasattr(user, 'employee_profile') and user.employee_profile:
            company = user.employee_profile.company
        qs = Ticket.objects.filter(company=company) if company else Ticket.objects.none()
    else:
        employee = getattr(user, 'employee_profile', None)
        if employee:
            qs = Ticket.objects.filter(Q(employee=employee) | Q(created_by=user))
        else:
            qs = Ticket.objects.filter(created_by=user)

    ticket = get_object_or_404(qs.select_related('company', 'employee__user', 'assigned_staff', 'created_by'), pk=pk)
    replies = ticket.replies.select_related('sender').order_by('created_at')
    escalations = ticket.escalations.select_related('escalated_to').order_by('created_at')

    reply_form = TicketReplyForm()
    status_form = None
    escalate_form = None

    if user.is_hryup_staff or user.is_hryup_admin:
        status_form = TicketStatusForm(instance=ticket)
        escalate_form = TicketEscalationForm(company=ticket.company)

    if request.method == 'POST':
        if 'add_reply' in request.POST:
            reply_form = TicketReplyForm(request.POST)
            if reply_form.is_valid():
                reply = reply_form.save(commit=False)
                reply.ticket = ticket
                reply.sender = user
                reply.company = ticket.company
                reply.save()

                # If staff replies to a ticket that is Open, advance to In Progress
                if (user.is_hryup_staff or user.is_hryup_admin) and ticket.status == 'Open':
                    ticket.status = 'In Progress'
                    if not ticket.assigned_staff and user.is_hryup_staff:
                        ticket.assigned_staff = user
                    ticket.save()

                messages.success(request, "Your reply has been posted.")
                return redirect('helpdesk:ticket_detail', pk=ticket.pk)
        
        elif 'update_status' in request.POST and (user.is_hryup_staff or user.is_hryup_admin):
            status_form = TicketStatusForm(request.POST, instance=ticket)
            if status_form.is_valid():
                status_form.save()
                messages.success(request, f"Ticket status changed to '{ticket.get_status_display()}'.")
                return redirect('helpdesk:ticket_detail', pk=ticket.pk)

    return render(request, 'helpdesk/ticket_detail.html', {
        'ticket': ticket,
        'replies': replies,
        'escalations': escalations,
        'reply_form': reply_form,
        'status_form': status_form,
        'escalate_form': escalate_form,
    })

@login_required
def ticket_escalate(request, pk):
    user = request.user
    if not (user.is_hryup_staff or user.is_hryup_admin):
        messages.error(request, "You are not authorized to escalate tickets.")
        return redirect('helpdesk:ticket_list')

    ticket = get_object_or_404(Ticket.objects.all(), pk=pk)

    if request.method == 'POST':
        form = TicketEscalationForm(request.POST, company=ticket.company)
        if form.is_valid():
            escalation = form.save(commit=False)
            escalation.ticket = ticket
            escalation.company = ticket.company
            escalation.save()
            ticket.status = 'Waiting on Client'
            ticket.save(update_fields=['status'])
            messages.success(request, f"Ticket has been escalated to {escalation.escalated_to.get_full_name()}.")
            return redirect('helpdesk:ticket_detail', pk=ticket.pk)
    
    return redirect('helpdesk:ticket_detail', pk=ticket.pk)
