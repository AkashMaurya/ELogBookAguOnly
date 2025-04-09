from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
import os
from admin_section.models import *
from accounts.models import Student, Doctor
from student_section.models import SupportTicket , StudentLogFormModel
from doctor_section.models import DoctorSupportTicket
from student_section.forms import AdminResponseForm
from doctor_section.forms import AdminDoctorResponseForm
from django.core.paginator import Paginator


# Django predefied models
from django.db.models import Count
from django.db.models.functions import TruncMonth
from datetime import timedelta


# Create your views here.


@login_required
def admin_dash(request):
    # Get filter parameters
    department_id = request.GET.get('department')

    # Get all departments
    departments = Department.objects.all()

    # Base queryset for logs
    logs = StudentLogFormModel.objects.all()
    doctors = Doctor.objects.all()

    if department_id:
        logs = logs.filter(department_id=department_id)
        doctors = doctors.filter(departments__id=department_id)

    # Get current date and start of month
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Performance metrics
    performance_data = {
        'total_logs': logs.count(),
        'total_doctors': doctors.count(),
        'total_students': Student.objects.count(),
        'departments_count': departments.count(),
        'pending_reviews': logs.filter(is_reviewed=False).count(),
        'monthly_submissions': logs.filter(created_at__gte=start_of_month).count(),
        'approval_rate': calculate_approval_rate(logs),
    }

    # Chart data
    chart_data = {
        'daily_submissions': get_daily_submissions_data(logs),
        'department_stats': get_department_stats(departments),
        'review_status': get_review_status_data(logs),
        'monthly_trend': get_monthly_trend_data(logs),
    }

    context = {
        'performance_data': performance_data,
        'chart_data': chart_data,
        'departments': departments,
        'selected_department': department_id,
    }

    return render(request, "admin_section/admin_dash.html", context)

def calculate_approval_rate(logs):
    reviewed_logs = logs.filter(is_reviewed=True)
    total_reviewed = reviewed_logs.count()
    if total_reviewed == 0:
        return 0
    approved = reviewed_logs.filter(reviewer_comments__startswith='REJECTED').count()
    return round((1 - approved / total_reviewed) * 100)

def get_daily_submissions_data(logs):
    last_7_days = timezone.now() - timedelta(days=7)
    daily_submissions = logs.filter(
        created_at__gte=last_7_days
    ).values('created_at__date').annotate(
        count=Count('id')
    ).order_by('created_at__date')

    return {
        'labels': [d['created_at__date'].strftime('%Y-%m-%d') for d in daily_submissions],
        'data': [d['count'] for d in daily_submissions]
    }

def get_department_stats(departments):
    dept_stats = []
    for dept in departments:
        logs = StudentLogFormModel.objects.filter(department=dept)
        total = logs.count()
        reviewed = logs.filter(is_reviewed=True).count()
        dept_stats.append({
            'name': dept.name,
            'total': total,
            'reviewed': reviewed,
            'pending': total - reviewed,
            'doctors_count': dept.doctors.count()
        })
    return dept_stats

def get_review_status_data(logs):
    total = logs.count()
    reviewed = logs.filter(is_reviewed=True).count()
    return {
        'labels': ['Reviewed', 'Pending'],
        'data': [reviewed, total - reviewed]
    }

def get_monthly_trend_data(logs):
    last_6_months = timezone.now() - timedelta(days=180)
    monthly_data = logs.filter(
        created_at__gte=last_6_months
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    return {
        'labels': [d['month'].strftime('%B %Y') for d in monthly_data],
        'data': [d['count'] for d in monthly_data]
    }


@login_required
def admin_blogs(request):
    return render(request, "admin_section/admin_blogs.html")


@login_required
def admin_profile(request):
    # Get the currently logged-in user from the request
    user = request.user

    # Get the profile photo URL
    if user.profile_photo:
        profile_photo = user.profile_photo.url
    else:
        profile_photo = "/media/profiles/default.jpg"  # Default image if no profile photo

    # Get user information
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    full_name = user.get_full_name() or username
    user_email = user.email
    user_role = user.role
    user_city = user.city
    user_country = user.country
    user_phone = user.phone_no
    user_speciality = user.speciality

    # Prepare the context dictionary with all the necessary data
    data = {
        "username": username,
        "full_name": full_name,
        "profile_photo": profile_photo,
        "user_role": user_role,
        "first_name": first_name,
        "last_name": last_name,
        "user_city": user_city,
        "user_country": user_country,
        "user_phone": user_phone,
        "user_speciality": user_speciality,
        "user_email": user_email,
    }

    return render(request, "admin_section/admin_profile.html", data)


@login_required
def admin_reviews(request):
    # Get filter parameters
    department_id = request.GET.get('department')
    status = request.GET.get('status', 'pending')
    search_query = request.GET.get('q', '').strip()

    # Get all departments for the filter
    all_departments = Department.objects.all()

    # Base queryset - for admin, show logs from all departments
    logs = StudentLogFormModel.objects.all()

    # Filter by review status
    if status == 'pending':
        logs = logs.filter(is_reviewed=False)
    elif status == 'reviewed':
        logs = logs.filter(is_reviewed=True)
    # If 'all' is selected, don't apply any filter

    # Filter by specific department if selected
    if department_id:
        logs = logs.filter(department_id=department_id)

    # Apply search query if provided
    if search_query:
        logs = logs.filter(
            models.Q(student__user__first_name__icontains=search_query) |
            models.Q(student__user__last_name__icontains=search_query) |
            models.Q(student__student_id__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(patient_id__icontains=search_query)
        )

    # Order by most recent first
    logs = logs.order_by('-date', '-created_at')

    # Pagination
    paginator = Paginator(logs, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Create batch review form
    from doctor_section.forms import BatchReviewForm
    batch_form = BatchReviewForm()

    context = {
        'logs': page_obj,
        'departments': all_departments,
        'selected_department': department_id,
        'selected_status': status,
        'search_query': search_query,
        'batch_form': batch_form,
    }

    return render(request, "admin_section/admin_reviews.html", context)


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
def update_contact_info(request):
    if request.method == "POST":
        phone = request.POST.get("phone")
        city = request.POST.get("city")
        country = request.POST.get("country")

        try:
            # Update user profile info
            user = request.user
            user.phone_no = phone
            user.city = city
            user.country = country
            user.save()

            # Update session data
            request.session["phone_no"] = phone
            request.session["city"] = city
            request.session["country"] = country
            request.session.modified = True

            return JsonResponse(
                {
                    "success": True,
                    "phone": phone,
                    "city": city,
                    "country": country,
                }
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def update_profile_photo(request):
    if request.method == "POST" and request.FILES.get("profile_photo"):
        user = request.user
        # Delete old profile photo if it exists and it's not the default
        if user.profile_photo and hasattr(user.profile_photo, "path") and "default.jpg" not in user.profile_photo.path:
            try:
                if os.path.exists(user.profile_photo.path):
                    os.remove(user.profile_photo.path)
            except Exception as e:
                print(f"Error deleting old profile photo: {e}")

        # Save new profile photo
        user.profile_photo = request.FILES["profile_photo"]
        user.save()

        return JsonResponse({"success": True, "profile_photo": user.profile_photo.url})

    return JsonResponse({"success": False, "error": "No photo provided"})


@login_required
def review_log(request, log_id):
    # Get the log
    log = get_object_or_404(StudentLogFormModel, id=log_id)

    if request.method == 'POST':
        # Import the form here to avoid circular imports
        from doctor_section.forms import LogReviewForm
        form = LogReviewForm(request.POST, instance=log)
        if form.is_valid():
            # Save the form but don't commit yet
            log_entry = form.save(commit=False)

            # Set review status based on the form choice
            is_approved = form.cleaned_data['is_approved']
            log_entry.is_reviewed = True

            # Add rejection prefix to comments if rejected
            if is_approved == 'False':
                prefix = "REJECTED: "
                if not log_entry.reviewer_comments.startswith(prefix):
                    log_entry.reviewer_comments = prefix + log_entry.reviewer_comments

            # Set review date
            log_entry.review_date = timezone.now()
            log_entry.save()

            messages.success(request, f"Log entry has been {'approved' if is_approved == 'True' else 'rejected'}.")
            return redirect('admin_section:admin_reviews')
    else:
        # Import the form here to avoid circular imports
        from doctor_section.forms import LogReviewForm
        form = LogReviewForm(instance=log)

    context = {
        'form': form,
        'log': log,
    }

    return render(request, 'admin_section/admin_review_log.html', context)


@login_required
def batch_review(request):
    if request.method != 'POST':
        return redirect('admin_section:admin_reviews')

    # Import the form here to avoid circular imports
    from doctor_section.forms import BatchReviewForm
    form = BatchReviewForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid form submission.")
        return redirect('admin_section:admin_reviews')

    # Get form data
    log_ids = form.cleaned_data['log_ids'].split(',')
    action = form.cleaned_data['action']
    comments = form.cleaned_data['comments']

    # Get logs - admin can review all logs
    logs = StudentLogFormModel.objects.filter(id__in=log_ids)

    # Process each log
    with transaction.atomic():
        for log in logs:
            log.is_reviewed = True
            log.review_date = timezone.now()

            # Set comments based on action
            if action == 'reject':
                prefix = "REJECTED: "
                log.reviewer_comments = prefix + comments if comments else prefix + "Batch rejected"
            else:  # approve
                log.reviewer_comments = comments if comments else "Approved"

            log.save()

    count = logs.count()
    messages.success(request, f"{count} log entries have been {'approved' if action == 'approve' else 'rejected'}.")
    return redirect('admin_section:admin_reviews')


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
