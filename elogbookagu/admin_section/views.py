from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import transaction, models
import os
import csv
import io
from datetime import timedelta
from django.contrib.auth.hashers import make_password

# Models
from admin_section.models import *
from accounts.models import CustomUser, Student, Doctor, Staff
from student_section.models import SupportTicket, StudentLogFormModel
from doctor_section.models import DoctorSupportTicket

# Forms
from .forms import BulkUserUploadForm, CSVUploadForm
from student_section.forms import AdminResponseForm
from doctor_section.forms import AdminDoctorResponseForm, BatchReviewForm, LogReviewForm
from django.core.paginator import Paginator

# Django predefined models
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth

@login_required
def bulk_add_users(request):
    if request.user.role != 'admin':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')

    if request.method == 'POST':
        form = BulkUserUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']

            # Validate file size (5MB limit)
            if csv_file.size > 5 * 1024 * 1024:
                messages.error(request, 'File size must be less than 5MB')
                return redirect('admin_section:bulk_add_users')

            try:
                decoded_file = csv_file.read().decode('utf-8')
            except UnicodeDecodeError:
                messages.error(request, 'Please upload a valid CSV file')
                return redirect('admin_section:bulk_add_users')

            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)

            # Basic required fields for all user types
            required_fields = [
                'username', 'first_name', 'last_name', 'email',
                'password', 'role', 'city', 'country', 'phone_no'
            ]

            # Validate headers
            headers = reader.fieldnames
            if not headers or not all(field in headers for field in required_fields):
                messages.error(request, 'CSV file must contain all required fields')
                return redirect('admin_section:bulk_add_users')

            success_count = 0
            error_count = 0
            error_messages = []

            for row in reader:
                try:
                    with transaction.atomic():
                        # Basic validation
                        username = row.get('username', '').strip()
                        email = row.get('email', '').strip()
                        role = row.get('role', '').strip().lower()

                        if not username or not email or not role:
                            raise ValueError("Username, email and role are required")

                        if CustomUser.objects.filter(username=username).exists():
                            raise ValueError(f"Username '{username}' already exists")

                        if CustomUser.objects.filter(email=email).exists():
                            raise ValueError(f"Email '{email}' already exists")

                        if role not in ['admin', 'student', 'doctor', 'staff']:
                            raise ValueError(f"Invalid role: {role}")

                        # Create user
                        user = CustomUser.objects.create(
                            username=username,
                            email=email,
                            password=make_password(row['password'].strip()),
                            first_name=row.get('first_name', '').strip(),
                            last_name=row.get('last_name', '').strip(),
                            role=role,
                            phone_no=row.get('phone_no', '').strip(),
                            city=row.get('city', '').strip(),
                            country=row.get('country', '').strip(),
                            bio=row.get('bio', '').strip(),
                            speciality=row.get('speciality', '').strip()
                        )

                        # Create role-specific profile
                        if role == 'student':
                            # Additional validation for student-specific fields
                            student_id = row.get('student_id', '').strip()
                            group_id = row.get('group', '').strip()

                            if not student_id:
                                raise ValueError("Student ID is required for student users")

                            if Student.objects.filter(student_id=student_id).exists():
                                raise ValueError(f"Student ID '{student_id}' already exists")

                            # Create student profile
                            student = Student(user=user, student_id=student_id)

                            # Assign group if provided and valid
                            if group_id:
                                try:
                                    group = Group.objects.get(id=group_id)
                                    student.group = group
                                except Group.DoesNotExist:
                                    # Try to match by group name (B1, B2, A1, etc.)
                                    try:
                                        group = Group.objects.filter(group_name=group_id).first()
                                        if group:
                                            student.group = group
                                    except Exception:
                                        pass

                            student.save()

                        elif role == 'doctor':
                            Doctor.objects.create(user=user)

                        elif role == 'staff':
                            Staff.objects.create(user=user)

                        success_count += 1
                except Exception as e:
                    error_count += 1
                    error_messages.append(f"Row {reader.line_num}: {str(e)}")

            if success_count > 0:
                messages.success(request, f"Successfully added {success_count} users.")
            if error_count > 0:
                messages.warning(request, f"Failed to add {error_count} users. See details below.")

            return render(request, 'admin_section/bulk_add_users.html', {
                'form': form,
                'results': {
                    'success_count': success_count,
                    'error_count': error_count,
                    'error_messages': error_messages[:10],
                    'total_errors': len(error_messages)
                }
            })
    else:
        form = BulkUserUploadForm()

    return render(request, 'admin_section/bulk_add_users.html', {'form': form})

# Create your views here.

@login_required
def admin_dash(request):
    # Check if user wants to use Streamlit dashboard
    use_streamlit = request.GET.get('streamlit', 'false').lower() == 'true'

    if use_streamlit:
        return redirect('admin_section:streamlit_dashboard')

    # Get filter parameters
    department_id = request.GET.get('department')
    student_search = request.GET.get('student_search', '')

    # Get all departments
    departments = Department.objects.all().order_by('name')

    # Base queryset for logs
    logs = StudentLogFormModel.objects.select_related('student', 'student__user', 'department', 'activity_type', 'core_diagnosis').all()
    doctors = Doctor.objects.select_related('user').prefetch_related('departments').all()
    students = Student.objects.select_related('user', 'group').all()
    activities = ActivityType.objects.all()

    # Filter logs by department if selected
    if department_id:
        logs = logs.filter(department_id=department_id)
        doctors = doctors.filter(departments__id=department_id)

    # Get current date and start of month
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Count metrics
    total_logs = logs.count()
    total_doctors = Doctor.objects.count()
    total_student = Student.objects.count()
    total_departments = Department.objects.count()
    total_activities = ActivityType.objects.count()

    # Review status counts
    reviewed_logs = logs.filter(is_reviewed=True)
    pending_logs = logs.filter(is_reviewed=False).count()
    approved_logs = reviewed_logs.exclude(reviewer_comments__startswith='REJECTED').count()
    rejected_logs = reviewed_logs.filter(reviewer_comments__startswith='REJECTED').count()

    # Get recent logs for the table (limited to 10)
    recent_logs = logs.order_by('-created_at')[:10]

    # Department statistics for charts
    department_stats = []
    for dept in departments:
        dept_logs = StudentLogFormModel.objects.filter(department=dept)
        total = dept_logs.count()
        reviewed = dept_logs.filter(is_reviewed=True).count()
        pending = total - reviewed
        department_stats.append({
            'name': dept.name,
            'total': total,
            'reviewed': reviewed,
            'pending': pending,
            'doctors_count': dept.doctors.count()
        })

    # Doctor performance data if department is selected
    doctor_performance = []
    if department_id:
        for doctor in doctors:
            doctor_logs = logs.filter(tutor=doctor)
            reviewed = doctor_logs.filter(is_reviewed=True).count()
            approved = doctor_logs.filter(is_reviewed=True).exclude(reviewer_comments__startswith='REJECTED').count()
            rejected = doctor_logs.filter(is_reviewed=True, reviewer_comments__startswith='REJECTED').count()
            doctor_performance.append({
                'name': doctor.user.get_full_name() or doctor.user.username,
                'reviewed': reviewed,
                'approved': approved,
                'rejected': rejected
            })

    # Student performance search
    student_data = None
    student_performance_data = None
    if student_search:
        # Search for student by name, ID or email
        student_query = students.filter(
            Q(student_id__icontains=student_search) |
            Q(user__email__icontains=student_search) |
            Q(user__first_name__icontains=student_search) |
            Q(user__last_name__icontains=student_search)
        ).first()

        if student_query:
            # Get student logs
            student_logs = logs.filter(student=student_query)
            total_student_logs = student_logs.count()
            approved_student_logs = student_logs.filter(is_reviewed=True).exclude(reviewer_comments__startswith='REJECTED').count()
            pending_student_logs = student_logs.filter(is_reviewed=False).count()
            rejected_student_logs = student_logs.filter(is_reviewed=True, reviewer_comments__startswith='REJECTED').count()

            # Create student data dictionary
            student_data = {
                'name': student_query.user.get_full_name() or student_query.user.username,
                'id': student_query.student_id,
                'email': student_query.user.email,
                'total_logs': total_student_logs,
                'approved_logs': approved_student_logs,
                'pending_logs': pending_student_logs,
                'rejected_logs': rejected_student_logs
            }

            # Get performance by department
            student_departments = student_logs.values('department__name').annotate(
                total=Count('id'),
                approved=Count('id', filter=Q(is_reviewed=True) & ~Q(reviewer_comments__startswith='REJECTED')),
                pending=Count('id', filter=Q(is_reviewed=False)),
                rejected=Count('id', filter=Q(is_reviewed=True) & Q(reviewer_comments__startswith='REJECTED'))
            )

            student_performance_data = []
            for dept in student_departments:
                student_performance_data.append({
                    'department': dept['department__name'],
                    'total': dept['total'],
                    'approved': dept['approved'],
                    'pending': dept['pending'],
                    'rejected': dept['rejected']
                })

    # Prepare chart data
    chart_data = {
        'department_stats': department_stats
    }

    context = {
        'departments': departments,
        'selected_department': department_id,
        'total_logs': total_logs,
        'total_doctors': total_doctors,
        'total_student': total_student,
        'total_departments': total_departments,
        'total_activities': total_activities,
        'approved_logs': approved_logs,
        'pending_logs': pending_logs,
        'rejected_logs': rejected_logs,
        'recent_logs': recent_logs,
        'chart_data': chart_data,
        'doctor_performance': doctor_performance,
        'student_search': student_search,
        'student_data': student_data,
        'student_performance_data': student_performance_data
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
def get_user_data(request):
    """AJAX endpoint to get user data for the dashboard"""
    user_type = request.GET.get('user_type', '')

    if not user_type or user_type not in ['student', 'doctor', 'staff', 'admin']:
        return JsonResponse({'error': 'Invalid user type'}, status=400)

    data = {'count': 0, 'users': []}

    if user_type == 'student':
        students = Student.objects.select_related('user', 'group').all()[:10]
        data['count'] = Student.objects.count()

        for student in students:
            data['users'].append({
                'id': student.student_id,
                'name': student.user.get_full_name() or student.user.username,
                'email': student.user.email,
                'group': student.group.group_name if student.group else 'No Group'
            })

    elif user_type == 'doctor':
        doctors = Doctor.objects.select_related('user').prefetch_related('departments').all()[:10]
        data['count'] = Doctor.objects.count()

        for doctor in doctors:
            departments = [dept.name for dept in doctor.departments.all()]
            data['users'].append({
                'name': doctor.user.get_full_name() or doctor.user.username,
                'email': doctor.user.email,
                'departments': ', '.join(departments) if departments else 'No Department',
                'speciality': doctor.user.speciality or 'Not specified'
            })

    elif user_type == 'staff':
        staff = Staff.objects.select_related('user').prefetch_related('departments').all()[:10]
        data['count'] = Staff.objects.count()

        for staff_member in staff:
            departments = [dept.name for dept in staff_member.departments.all()]
            data['users'].append({
                'name': staff_member.user.get_full_name() or staff_member.user.username,
                'email': staff_member.user.email,
                'departments': ', '.join(departments) if departments else 'No Department'
            })

    elif user_type == 'admin':
        admins = CustomUser.objects.filter(role='admin')[:10]
        data['count'] = CustomUser.objects.filter(role='admin').count()

        for admin in admins:
            data['users'].append({
                'name': admin.get_full_name() or admin.username,
                'email': admin.email
            })

    return JsonResponse(data)

@login_required
def streamlit_dashboard(request):
    """Launch Streamlit dashboard in a new process"""
    if request.user.role != 'admin':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')

    # Get the path to the Streamlit script
    streamlit_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'streamlit_dashboard.py')

    # Check if the script exists
    if not os.path.exists(streamlit_script_path):
        messages.error(request, "Streamlit dashboard script not found.")
        return redirect('admin_section:admin_dash')

    # Launch Streamlit in a subprocess
    try:
        # Use a different port to avoid conflicts with Django
        port = 8501
        subprocess.Popen(
            [sys.executable, '-m', 'streamlit', 'run', streamlit_script_path, '--server.port', str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Redirect to the Streamlit dashboard
        return redirect(f'http://localhost:{port}')
    except Exception as e:
        messages.error(request, f"Failed to launch Streamlit dashboard: {str(e)}")
        return redirect('admin_section:admin_dash')


def download_user_template(request):
    """Download a sample CSV template for user import"""
    response = HttpResponse(content_type='text/csv')
    user_type = request.GET.get('type', 'general')

    if user_type == 'student':
        response['Content-Disposition'] = 'attachment; filename="student_import_template.csv"'

        # Write headers for student template
        headers = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'role', 'student_id', 'group', 'city', 'country', 'phone_no'
        ]
        writer = csv.writer(response)
        writer.writerow(headers)

        # Write sample data for student with different group names
        sample_data = [
            'student1', 'student1@example.com', 'SecurePass123', 'John', 'Student',
            'student', 'STU12345', 'B1', 'New York', 'USA', '1234567890'
        ]
        writer.writerow(sample_data)

        # Add more examples with different groups
        sample_data2 = [
            'student2', 'student2@example.com', 'SecurePass456', 'Jane', 'Student',
            'student', 'STU67890', 'A2', 'London', 'UK', '9876543210'
        ]
        writer.writerow(sample_data2)

        sample_data3 = [
            'student3', 'student3@example.com', 'SecurePass789', 'Alex', 'Student',
            'student', 'STU24680', 'B2', 'Paris', 'France', '5555555555'
        ]
        writer.writerow(sample_data3)

        sample_data4 = [
            'student4', 'student4@example.com', 'SecurePass101', 'Maria', 'Student',
            'student', 'STU13579', 'A1', 'Berlin', 'Germany', '6666666666'
        ]
        writer.writerow(sample_data4)

    elif user_type == 'doctor':
        response['Content-Disposition'] = 'attachment; filename="doctor_import_template.csv"'

        # Write headers for doctor template
        headers = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'role', 'speciality', 'city', 'country', 'phone_no', 'bio'
        ]
        writer = csv.writer(response)
        writer.writerow(headers)

        # Write sample data for doctor
        sample_data = [
            'doctor1', 'doctor1@example.com', 'SecurePass123', 'John', 'Doctor',
            'doctor', 'Cardiology', 'New York', 'USA', '1234567890', 'Experienced cardiologist'
        ]
        writer.writerow(sample_data)

    elif user_type == 'staff':
        response['Content-Disposition'] = 'attachment; filename="staff_import_template.csv"'

        # Write headers for staff template
        headers = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'role', 'city', 'country', 'phone_no'
        ]
        writer = csv.writer(response)
        writer.writerow(headers)

        # Write sample data for staff
        sample_data = [
            'staff1', 'staff1@example.com', 'SecurePass123', 'John', 'Staff',
            'staff', 'New York', 'USA', '1234567890'
        ]
        writer.writerow(sample_data)

    else:
        # Default general template
        response['Content-Disposition'] = 'attachment; filename="user_import_template.csv"'

        # Write headers for general template
        headers = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'role', 'city', 'country', 'phone_no', 'bio', 'speciality'
        ]
        writer = csv.writer(response)
        writer.writerow(headers)

        # Write sample data
        sample_data = [
            'john.doe', 'john@example.com', 'SecurePass123', 'John', 'Doe',
            'doctor', 'New York', 'USA', '1234567890', 'Experienced doctor', 'Cardiology'
        ]
        writer.writerow(sample_data)

    return response

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


@login_required
def notifications(request):
    return render(request, 'admin_section/notifications.html')


@login_required
def bulk_import_users(request):
    if request.user.role != 'admin':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')

    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            user_type = form.cleaned_data['user_type']

            # Validate file size (5MB limit)
            if csv_file.size > 5 * 1024 * 1024:
                messages.error(request, 'File size must be less than 5MB')
                return redirect('admin_section:bulk_import_users')

            try:
                decoded_file = csv_file.read().decode('utf-8')
            except UnicodeDecodeError:
                messages.error(request, 'Please upload a valid CSV file')
                return redirect('admin_section:bulk_import_users')

            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)

            # Basic required fields for all user types
            required_fields = [
                'username', 'email', 'password', 'first_name', 'last_name',
                'city', 'country', 'phone_no'
            ]

            # Add role-specific required fields
            if user_type == 'student':
                required_fields.append('student_id')

            # Validate headers
            headers = reader.fieldnames
            if not headers or not all(field in headers for field in required_fields):
                missing_fields = [field for field in required_fields if field not in headers]
                messages.error(request, f'CSV file is missing required fields: {", ".join(missing_fields)}')
                return redirect('admin_section:bulk_import_users')

            success_count = 0
            error_count = 0
            error_messages = []

            for row in reader:
                try:
                    with transaction.atomic():
                        # Basic validation
                        username = row.get('username', '').strip()
                        email = row.get('email', '').strip()

                        if not username or not email:
                            raise ValueError("Username and email are required")

                        if CustomUser.objects.filter(username=username).exists():
                            raise ValueError(f"Username '{username}' already exists")

                        if CustomUser.objects.filter(email=email).exists():
                            raise ValueError(f"Email '{email}' already exists")

                        # Create user with role based on form selection
                        user = CustomUser.objects.create(
                            username=username,
                            email=email,
                            password=make_password(row['password'].strip()),
                            first_name=row.get('first_name', '').strip(),
                            last_name=row.get('last_name', '').strip(),
                            role=user_type,  # Use the selected role from the form
                            phone_no=row.get('phone_no', '').strip(),
                            city=row.get('city', '').strip(),
                            country=row.get('country', '').strip(),
                            bio=row.get('bio', '').strip(),
                            speciality=row.get('speciality', '').strip()
                        )

                        # Create role-specific profile
                        if user_type == 'student':
                            # Additional validation for student-specific fields
                            student_id = row.get('student_id', '').strip()
                            group_id = row.get('group', '').strip()

                            if not student_id:
                                raise ValueError("Student ID is required for student users")

                            if Student.objects.filter(student_id=student_id).exists():
                                raise ValueError(f"Student ID '{student_id}' already exists")

                            # Create student profile
                            student = Student(user=user, student_id=student_id)

                            # Assign group if provided and valid
                            if group_id:
                                # First try to match by group name (B1, B2, A1, etc.)
                                group = Group.objects.filter(group_name=group_id).first()

                                # If not found by name, try by ID (if it's a number)
                                if not group and group_id.isdigit():
                                    try:
                                        group = Group.objects.get(id=int(group_id))
                                    except Group.DoesNotExist:
                                        pass

                                # If group was found, assign it
                                if group:
                                    student.group = group
                                else:
                                    # Log a warning but don't fail the import
                                    print(f"Warning: Group '{group_id}' not found for student {student_id}")

                            student.save()

                        elif user_type == 'doctor':
                            Doctor.objects.create(user=user)

                        elif user_type == 'staff':
                            Staff.objects.create(user=user)

                        success_count += 1
                except Exception as e:
                    error_count += 1
                    error_messages.append(f"Row {reader.line_num}: {str(e)}")

            if success_count > 0:
                messages.success(request, f"Successfully added {success_count} {user_type}s.")
            if error_count > 0:
                messages.warning(request, f"Failed to add {error_count} {user_type}s. See details below.")

            return render(request, 'admin_section/bulk_import_users.html', {
                'form': form,
                'results': {
                    'success_count': success_count,
                    'error_count': error_count,
                    'error_messages': error_messages[:10],
                    'total_errors': len(error_messages),
                    'user_type': user_type
                }
            })
    else:
        form = CSVUploadForm()

    return render(request, 'admin_section/bulk_import_users.html', {'form': form})

@login_required
def download_sample_csv(request):
    """Download a sample CSV template for student import"""
    # This function is kept for backward compatibility
    # Redirect to the download_user_template function with type=student
    return download_user_template(request)
