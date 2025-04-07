from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from admin_section.models import *
from accounts.models import Student, Doctor
from student_section.models import SupportTicket
from doctor_section.models import DoctorSupportTicket
from student_section.forms import AdminResponseForm
from doctor_section.forms import AdminDoctorResponseForm

# Django predefied models
from django.db.models import Count


# Create your views here.


@login_required
def admin_dash(request):
    # Counting
    total_activities = ActivityType.objects.count()
    total_departments = Department.objects.count()

    total_student = Student.objects.count()
    total_doctors = Doctor.objects.count()



    print(total_student)
    data = {
        "total_activities": total_activities,
        "total_departments": total_departments,
        "total_student": total_student,
        "total_doctors": total_doctors,
    }

    return render(request, "admin_section/admin_dash.html", data)


@login_required
def admin_blogs(request):
    return render(request, "admin_section/admin_blogs.html")


@login_required
def admin_profile(request):
    return render(request, "admin_section/admin_profile.html")


@login_required
def admin_reviews(request):
    return render(request, "admin_section/admin_reviews.html")


@login_required
def admin_support(request):
    # Get ticket type filter
    ticket_type = request.GET.get('type', 'student')
    status_filter = request.GET.get('status', '')

    # Get appropriate tickets based on type
    if ticket_type == 'doctor':
        tickets = DoctorSupportTicket.objects.all().order_by('-date_created')
    else:  # default to student tickets
        tickets = SupportTicket.objects.all().order_by('-date_created')
        ticket_type = 'student'  # ensure valid value

    # Apply status filter if provided
    if status_filter in ['pending', 'solved']:
        tickets = tickets.filter(status=status_filter)

    context = {
        'tickets': tickets,
        'status_filter': status_filter,
        'ticket_type': ticket_type,
    }
    return render(request, "admin_section/admin_support.html", context)


@login_required
def final_records(request):
    return render(request, "admin_section/admin_final_record.html")


@login_required
def resolve_ticket(request, ticket_id):
    # Check if it's a student or doctor ticket
    ticket_type = request.GET.get('type', 'student')

    if ticket_type == 'doctor':
        ticket = get_object_or_404(DoctorSupportTicket, id=ticket_id)
        form_class = AdminDoctorResponseForm
    else:  # default to student ticket
        ticket = get_object_or_404(SupportTicket, id=ticket_id)
        form_class = AdminResponseForm

    if request.method == 'POST':
        form = form_class(request.POST, instance=ticket)
        if form.is_valid():
            ticket = form.save(commit=False)
            if ticket.status == 'solved':
                ticket.resolved_date = timezone.now()
            ticket.save()
            messages.success(request, f"Ticket '{ticket.subject}' has been updated successfully.")
            return redirect(f"/admin_section/admin_support/?type={ticket_type}")
    else:
        form = form_class(instance=ticket)

    context = {
        'form': form,
        'ticket': ticket,
        'ticket_type': ticket_type,
    }
    return render(request, 'admin_section/resolve_ticket.html', context)
