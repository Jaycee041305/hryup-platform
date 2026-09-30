from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Ticket, TicketReply, TicketEscalation
from .forms import TicketForm, TicketReplyForm, TicketStatusForm, TicketEscalationForm

@login_required
def ticket_list(request):
    user = request.user
    if user.is_hryup_admin or user.is_hryup_staff:
        # Staff see all tickets (or assigned to them). For simplicity, let's show all or their assigned.
        # Could filter by company if they are assigned specific ones, but let's show all tickets.
        if user.is_hryup_staff:
            tickets = Ticket.objects.filter(Q(assigned_staff=user) | Q(assigned_staff__isnull=True)).order_by('-created_at')
        else:
            tickets = Ticket.objects.all().order_by('-created_at')
    elif user.is_client_manager:
        # Manager sees tickets for their company
        company = user.get_company()
        tickets = Ticket.objects.filter(company=company).order_by('-created_at')
    else:
        # Client employee sees only their own tickets
        company = user.get_company()
        tickets = Ticket.objects.filter(company=company, employee=user.employee_profile).order_by('-created_at')

    return render(request, 'helpdesk/ticket_list.html', {'tickets': tickets})

@login_required
def ticket_submit(request):
    if not request.user.is_client_employee and not request.user.is_client_manager:
        messages.error(request, "Only client employees can submit tickets.")
        return redirect('helpdesk:ticket_list')

    company = request.user.get_company()
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.company = company
            ticket.employee = request.user.employee_profile
            ticket.save()
            messages.success(request, "Ticket submitted successfully.")
            return redirect('helpdesk:ticket_detail', pk=ticket.pk)
    else:
        form = TicketForm()

    return render(request, 'helpdesk/ticket_form.html', {'form': form})

@login_required
def ticket_detail(request, pk):
    user = request.user
    # Base queryset for checking access
    if user.is_hryup_admin or user.is_hryup_staff:
        qs = Ticket.objects.all()
    elif user.is_client_manager:
        qs = Ticket.objects.filter(company=user.get_company())
    else:
        qs = Ticket.objects.filter(employee=user.employee_profile)

    ticket = get_object_or_404(qs, pk=pk)
    replies = ticket.replies.all().order_by('created_at')
    escalations = ticket.escalations.all().order_by('created_at')

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
                messages.success(request, "Reply added.")
                return redirect('helpdesk:ticket_detail', pk=ticket.pk)
        
        elif 'update_status' in request.POST and (user.is_hryup_staff or user.is_hryup_admin):
            status_form = TicketStatusForm(request.POST, instance=ticket)
            if status_form.is_valid():
                status_form.save()
                messages.success(request, "Ticket status updated.")
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
        messages.error(request, "Not authorized.")
        return redirect('helpdesk:ticket_list')

    ticket = get_object_or_404(Ticket.objects.all(), pk=pk)

    if request.method == 'POST':
        form = TicketEscalationForm(request.POST, company=ticket.company)
        if form.is_valid():
            escalation = form.save(commit=False)
            escalation.ticket = ticket
            escalation.company = ticket.company
            escalation.save()
            messages.success(request, "Ticket escalated successfully.")
            return redirect('helpdesk:ticket_detail', pk=ticket.pk)
    
    return redirect('helpdesk:ticket_detail', pk=ticket.pk)
