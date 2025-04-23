# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction, models
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncMonth
from datetime import timedelta
from accounts.models import Staff
from student_section.models import StudentLogFormModel
from admin_section.models import Department
from .forms import LogReviewForm, BatchReviewForm, ProfileUpdateForm

# Staff Dashboard View

@login_required
def staff_dash(request):
    user = request.user

    # Check if user has staff role
    if user.role != 'staff':
        messages.error(request, 'You do not have permission to access the staff dashboard.')
        return redirect('login')

    try:
        staff = user.staff_profile
    except Staff.DoesNotExist:
        # Create staff profile if it doesn't exist
        staff = Staff.objects.create(user=user)
        messages.success(request, 'Staff profile has been created successfully.')

    # Ensure session data is available
    if 'first_name' not in request.session:
        request.session['first_name'] = user.first_name
        request.session['last_name'] = user.last_name
        request.session['email'] = user.email
        request.session.save()

    # Get filter parameters
    selected_department = request.GET.get('department')
    search_query = request.GET.get('search', '').strip()

    # Get staff's departments
    departments = staff.departments.all()

    # Base queryset for logs - filter by departments the staff is associated with
    logs = StudentLogFormModel.objects.filter(department__in=departments)

    # Get all doctors in staff's departments
    from accounts.models import Doctor
    department_doctors = Doctor.objects.filter(departments__in=departments).distinct()

    # Filter by selected department if provided
    if selected_department:
        # Ensure the selected department is one of the staff's departments
        try:
            selected_dept = Department.objects.get(id=selected_department)
            if selected_dept in departments:
                logs = logs.filter(department=selected_dept)
                # Also filter doctors by the selected department
                department_doctors = department_doctors.filter(departments=selected_dept)
            else:
                # If the department doesn't belong to the staff, ignore the filter
                selected_department = None
        except Department.DoesNotExist:
            # If the department doesn't exist, ignore the filter
            selected_department = None

    # We've removed the doctor filter functionality

    # Filter doctors by search query if provided
    filtered_doctors = department_doctors
    if search_query:
        filtered_doctors = department_doctors.filter(
            models.Q(user__first_name__icontains=search_query) |
            models.Q(user__last_name__icontains=search_query) |
            models.Q(user__email__icontains=search_query) |
            models.Q(user__username__icontains=search_query) |
            models.Q(user__speciality__icontains=search_query)
        )

    # Get current date and start of month
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Get accurate counts for performance metrics
    reviewed_logs = StudentLogFormModel.objects.filter(
        department__in=departments,
        is_reviewed=True
    )

    pending_logs = StudentLogFormModel.objects.filter(
        department__in=departments,
        is_reviewed=False
    )

    monthly_reviews = StudentLogFormModel.objects.filter(
        department__in=departments,
        is_reviewed=True,
        review_date__gte=start_of_month
    ).count()

    # Performance metrics
    performance_data = {
        'total_reviews': reviewed_logs.count(),
        'pending_reviews': pending_logs.count(),
        'monthly_reviews': monthly_reviews,
        'approval_rate': calculate_approval_rate(reviewed_logs),
    }

    # Chart data
    chart_data = {
        'daily_reviews': get_daily_reviews_data(logs),
        'department_stats': get_department_stats(logs, departments),
        'review_status': get_review_status_data(logs),
        'monthly_trend': get_monthly_trend_data(logs),
    }

    # Get accurate counts directly from the database
    # Total records in staff's departments
    total_records = StudentLogFormModel.objects.filter(department__in=departments).count()

    # Records that have been reviewed
    reviewed_count = StudentLogFormModel.objects.filter(
        department__in=departments,
        is_reviewed=True
    ).count()

    # Records left to review
    left_to_review = StudentLogFormModel.objects.filter(
        department__in=departments,
        is_reviewed=False
    ).count()

    # Double-check that counts are consistent
    if total_records != (reviewed_count + left_to_review):
        # If there's a discrepancy, recalculate to ensure consistency
        total_records = reviewed_count + left_to_review

    # Get doctor information for display
    doctors_info = []
    for doctor in filtered_doctors:
        # Get performance metrics for this doctor
        # Use tutor field instead of reviewer since there's no reviewer field
        doctor_logs = StudentLogFormModel.objects.filter(
            department__in=departments,
            tutor=doctor
        )

        # Count total logs and reviewed logs
        total_logs = doctor_logs.count()
        reviewed_logs = doctor_logs.filter(is_reviewed=True).count()
        monthly_logs = doctor_logs.filter(date__gte=start_of_month).count()

        doctors_info.append({
            'id': doctor.id,
            'name': doctor.user.get_full_name() or doctor.user.username,
            'email': doctor.user.email,
            'speciality': doctor.user.speciality,
            'departments': ', '.join([dept.name for dept in doctor.departments.all()]),
            'total_logs': total_logs,
            'reviewed_logs': reviewed_logs,
            'monthly_logs': monthly_logs,
            'review_percentage': round((reviewed_logs / total_logs * 100)) if total_logs > 0 else 0
        })

    # Calculate percentage for progress circle
    review_percentage = 0
    if total_records > 0:
        review_percentage = int((reviewed_count / total_records) * 100)

    context = {
        'staff': staff,
        'user': user,
        'performance_data': performance_data,
        'chart_data': chart_data,
        'departments': departments,
        'selected_department': selected_department,
        'search_query': search_query,
        'total_records': total_records,
        'left_to_review': left_to_review,
        'reviewed': reviewed_count,
        'review_percentage': review_percentage,
        'doctors': doctors_info,
        'today': today,
    }

    return render(request, "staff_section/staff_dash.html", context)

@login_required
# Staff Support View
def staff_support(request):
    if request.user.role != 'staff':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('login')
    return render(request, "staff_section/staff_support.html")

@login_required
# Staff Reviews View
def staff_reviews(request):
    if request.user.role != 'staff':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('login')

    staff = request.user.staff_profile

    # Get filter parameters
    department_id = request.GET.get('department')
    status = request.GET.get('status', 'pending')
    search_query = request.GET.get('q', '').strip()

    # Get departments associated with this staff
    staff_departments = staff.departments.all()

    # Base queryset - filter by departments the staff is associated with
    logs = StudentLogFormModel.objects.filter(department__in=staff_departments)

    # Filter by review status
    if status == 'pending':
        logs = logs.filter(is_reviewed=False)
    elif status == 'reviewed':
        logs = logs.filter(is_reviewed=True)
    # If 'all' is selected, don't apply any filter

    # Filter by specific department if selected
    if department_id:
        logs = logs.filter(department_id=department_id)

    # Apply search filter if provided
    if search_query:
        logs = logs.filter(
            models.Q(student__user__first_name__icontains=search_query) |
            models.Q(student__user__last_name__icontains=search_query) |
            models.Q(student__student_id__icontains=search_query) |
            models.Q(patient_id__icontains=search_query)
        )

    # Order by most recent first
    logs = logs.order_by('-date', '-created_at')

    # Pagination
    paginator = Paginator(logs, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Create batch review form
    batch_form = BatchReviewForm()

    context = {
        'logs': page_obj,
        'departments': staff_departments,
        'selected_department': department_id,
        'selected_status': status,
        'search_query': search_query,
        'batch_form': batch_form,
    }

    return render(request, "staff_section/staff_reviews.html", context)

@login_required
# Staff Profile View
def staff_profile(request):
    if request.user.role != 'staff':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('login')

    user = request.user
    try:
        staff = user.staff_profile
    except Staff.DoesNotExist:
        staff = Staff.objects.create(user=user)
        messages.info(request, 'Staff profile has been created.')

    # Get the profile photo URL
    profile_photo = user.profile_photo.url if user.profile_photo else "/media/profiles/default.jpg"

    # Handle form submission
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('staff_section:staff_profile')
        else:
            messages.error(request, 'There was an error updating your profile. Please check the form.')
    else:
        form = ProfileUpdateForm(instance=user)

    # Get staff departments
    departments = staff.departments.all()

    data = {
        "staff": staff,
        "profile_photo": profile_photo,
        "full_name": f"{user.first_name} {user.last_name}",
        "user_email": user.email,
        "user_phone": user.phone_no,
        "user_city": user.city,
        "user_country": user.country,
        "user_bio": user.bio if hasattr(user, "bio") else "",
        "form": form,
        "departments": departments,
    }

    return render(request, "staff_section/staff_profile.html", data)


def calculate_approval_rate(reviewed_logs):
    # reviewed_logs should already be filtered for is_reviewed=True
    total_reviewed = reviewed_logs.count()
    if total_reviewed == 0:
        return 0

    # Count rejected logs (those with REJECTED in comments)
    rejected = reviewed_logs.filter(reviewer_comments__startswith='REJECTED').count()

    # Calculate approval rate (percentage of non-rejected logs)
    return round((1 - rejected / total_reviewed) * 100)


def get_daily_reviews_data(logs):
    last_7_days = timezone.now() - timedelta(days=7)
    daily_reviews = logs.filter(
        review_date__gte=last_7_days
    ).values('review_date__date').annotate(
        count=Count('id')
    ).order_by('review_date__date')

    return {
        'labels': [d['review_date__date'].strftime('%Y-%m-%d') for d in daily_reviews],
        'data': [d['count'] for d in daily_reviews]
    }


def get_department_stats(logs, departments):
    dept_stats = []
    for dept in departments:
        # Get accurate counts for each department
        reviewed = StudentLogFormModel.objects.filter(
            department=dept,
            is_reviewed=True
        ).count()

        pending = StudentLogFormModel.objects.filter(
            department=dept,
            is_reviewed=False
        ).count()

        total = reviewed + pending

        dept_stats.append({
            'name': dept.name,
            'total': total,
            'reviewed': reviewed,
            'pending': pending
        })
    return dept_stats


def get_review_status_data(logs):
    # Get accurate counts directly
    reviewed = logs.filter(is_reviewed=True).count()
    pending = logs.filter(is_reviewed=False).count()
    total = reviewed + pending

    return {
        'labels': ['Reviewed', 'Pending'],
        'data': [reviewed, pending]
    }


def get_monthly_trend_data(logs):
    last_6_months = timezone.now() - timedelta(days=180)
    monthly_data = logs.filter(
        review_date__gte=last_6_months
    ).annotate(
        month=TruncMonth('review_date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    return {
        'labels': [d['month'].strftime('%B %Y') for d in monthly_data],
        'data': [d['count'] for d in monthly_data]
    }


@login_required
def review_log(request, log_id):
    if request.user.role != 'staff':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('login')

    # Get the log
    log = get_object_or_404(StudentLogFormModel, id=log_id)

    # Get staff departments
    staff = request.user.staff_profile
    staff_departments = staff.departments.all()

    # Check if the log belongs to a department the staff is associated with
    if log.department not in staff_departments:
        messages.error(request, 'You do not have permission to review this log.')
        return redirect('staff_section:staff_reviews')

    if request.method == 'POST':
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
            return redirect('staff_section:staff_reviews')
    else:
        form = LogReviewForm(instance=log)

    context = {
        'form': form,
        'log': log,
    }

    return render(request, 'staff_section/staff_review_log.html', context)


@login_required
def batch_review(request):
    if request.user.role != 'staff':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('login')

    if request.method != 'POST':
        return redirect('staff_section:staff_reviews')

    form = BatchReviewForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid form submission.")
        return redirect('staff_section:staff_reviews')

    # Get form data
    log_ids = form.cleaned_data['log_ids'].split(',')
    action = form.cleaned_data['action']
    comments = form.cleaned_data['comments']

    # Get the staff
    staff = request.user.staff_profile
    staff_departments = staff.departments.all()

    # Get logs that belong to the staff's departments
    logs = StudentLogFormModel.objects.filter(
        id__in=log_ids,
        department__in=staff_departments
    )

    if not logs.exists():
        messages.warning(request, "No logs found to review.")
        return redirect('staff_section:staff_reviews')

    # Process logs in a transaction
    with transaction.atomic():
        for log in logs:
            log.is_reviewed = True

            # Set comments if provided
            if comments:
                log.reviewer_comments = comments

            # Add rejection prefix if rejecting
            if action == 'reject':
                prefix = "REJECTED: "
                if not log.reviewer_comments.startswith(prefix):
                    log.reviewer_comments = prefix + log.reviewer_comments

            # Set review date
            log.review_date = timezone.now()
            log.save()

    messages.success(request, f"{logs.count()} log entries have been {'approved' if action == 'approve' else 'rejected'}.")
    return redirect('staff_section:staff_reviews')
