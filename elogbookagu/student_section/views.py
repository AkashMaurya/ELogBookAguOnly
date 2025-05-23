from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404
from django.core.paginator import Paginator
from django.db import models
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
from xhtml2pdf import pisa
from .forms import StudentLogFormModelForm, SupportTicketForm
from .models import StudentLogFormModel, SupportTicket, StudentNotification
from admin_section.models import ActivityType, CoreDiaProSession, LogYear, Department, AdminNotification, DateRestrictionSettings
from accounts.models import Doctor, Student, CustomUser
from django.contrib import messages
from doctor_section.models import Notification

# Create your views here.


@login_required
def student_dash(request):
    user = request.user
    student_group = Student.objects.select_related(
        "group", "group__log_year", "group__log_year_section"
    ).get(user=user)

    # count the log of student
    total_records = StudentLogFormModel.objects.filter(student=user.student).count()

    # yet to be reviewed

    yet_to_be_reviewed = StudentLogFormModel.objects.filter(
        student=user.student, is_reviewed=False
    ).count()

    # reviewed
    reviewed = StudentLogFormModel.objects.filter(
        student=user.student, is_reviewed=True
    ).count()

    if user.profile_photo:
        profile_photo = user.profile_photo.url
    else:
        profile_photo = "/media/profiles/default.jpg"

    data = {
        "total_records": total_records,
        "yet_to_be_reviewed": yet_to_be_reviewed,
        "reviewed": reviewed,
        "your_group": student_group.group,
        "profile_photo": profile_photo,
    }

    return render(request, "student_dash.html", data)




from django.db import transaction
from threading import Thread

def send_admin_emails(admin_emails, subject, message):
    """Send emails to admins in a separate thread"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=admin_emails,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error sending email: {e}")

@login_required
def student_support(request):
    if request.method == "POST":
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            # Use transaction to ensure all database operations succeed or fail together
            with transaction.atomic():
                ticket = form.save(commit=False)
                ticket.student = request.user.student
                ticket.save()

                # Create notification for admins
                student_name = request.user.get_full_name() or request.user.username
                notification_title = f"New Student Support Ticket: {ticket.subject}"
                notification_message = f"{student_name} has submitted a new support ticket: {ticket.subject}\n\n{ticket.description}"

                # Get all admin users - use values_list for efficiency
                admin_users = CustomUser.objects.filter(role='admin')
                admin_emails = list(admin_users.values_list('email', flat=True))

                # Bulk create notifications for all admins at once
                notifications = [
                    AdminNotification(
                        recipient=admin,
                        title=notification_title,
                        message=notification_message,
                        support_ticket_type='student',
                        ticket_id=ticket.id
                    ) for admin in admin_users
                ]

                if notifications:
                    AdminNotification.objects.bulk_create(notifications)

                # Start a separate thread to send emails
                if admin_emails:
                    email_thread = Thread(
                        target=send_admin_emails,
                        args=(admin_emails, notification_title, notification_message)
                    )
                    email_thread.daemon = True
                    email_thread.start()

            messages.success(request, "Support ticket submitted successfully. We will respond to your issue soon.")
            return redirect("student_section:student_support")
    else:
        form = SupportTicketForm()

    # Get all tickets for the current student
    tickets = SupportTicket.objects.filter(student=request.user.student).order_by('-date_created')

    context = {
        "form": form,
        "tickets": tickets,
    }
    return render(request, "student_support.html", context)


def send_tutor_email(tutor_email, subject, message):
    """Send email to tutor in a separate thread"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[tutor_email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error sending email: {e}")

@login_required
def student_elog(request):
    if request.method == "POST":
        form = StudentLogFormModelForm(request.POST, user=request.user)
        if form.is_valid():
            # Use transaction to ensure all database operations succeed or fail together
            with transaction.atomic():
                log_entry = form.save(commit=False)
                log_entry.student = request.user.student
                log_entry.log_year = request.user.student.group.log_year
                log_entry.log_year_section = request.user.student.group.log_year_section
                log_entry.group = request.user.student.group
                log_entry.save()

                # Get the department and tutor from the form
                department = form.cleaned_data['department']
                tutor = form.cleaned_data['tutor']

                # Create notification for the tutor
                student_name = request.user.get_full_name() or request.user.username
                notification_title = f"New Log Entry from {student_name}"
                notification_message = f"{student_name} has submitted a new log entry for {department.name} department on {log_entry.date}."

                # Create notification in the database
                Notification.objects.create(
                    recipient=tutor,
                    log_entry=log_entry,
                    title=notification_title,
                    message=notification_message
                )

                # Send email notification to the tutor in a separate thread
                if tutor.user.email:
                    email_thread = Thread(
                        target=send_tutor_email,
                        args=(tutor.user.email, notification_title, notification_message)
                    )
                    email_thread.daemon = True
                    email_thread.start()

            messages.success(request, "Log entry created successfully.")
            return redirect("student_section:student_elog")
    else:
        form = StudentLogFormModelForm(user=request.user)

    student = request.user.student
    context = {
        "form": form,
        "student_name": student.user.get_full_name(),
        "student_id": student.student_id,
        "year_name": student.group.log_year.year_name if student.group else "",
        "section_name": (
            student.group.log_year_section.year_section_name if student.group else ""
        ),
        "group_name": student.group.group_name if student.group else "",
    }
    return render(request, "student_elog.html", context)


@login_required
def student_profile(request):
    # Get the current user
    user = request.user

    # Get profile photo URL
    profile_photo = user.profile_photo.url if user.profile_photo else "/media/profiles/default.jpg"

    # Get student profile with related group data using select_related for efficiency
    try:
        student = Student.objects.select_related(
            "group", "group__log_year", "group__log_year_section"
        ).get(user=user)
    except Student.DoesNotExist:
        student = None

    # Initialize group information variables
    group_info = None
    log_year = None
    log_year_section = None
    group_full_info = None

    # Get group information if student exists and has a group
    if student and student.group:
        group = student.group
        group_info = group.group_name
        log_year = group.log_year.year_name if group.log_year else None
        log_year_section = group.log_year_section.year_section_name if group.log_year_section else None
        group_full_info = str(group)

    # Get statistics for the dashboard
    logs_count = 0
    approved_count = 0
    pending_count = 0
    departments_count = 0

    if student:
        # Get log statistics
        logs = StudentLogFormModel.objects.filter(student=student)
        logs_count = logs.count()
        approved_count = logs.filter(is_reviewed=True).exclude(
            reviewer_comments__startswith='REJECTED'
        ).count()
        pending_count = logs.filter(is_reviewed=False).count()

        # Get unique departments the student has submitted logs to
        departments_count = logs.values('department').distinct().count()

    # Prepare context data for the template
    data = {
        "profile_photo": profile_photo,
        "full_name": f"{user.first_name} {user.last_name}",
        "user_email": user.email,
        "user_phone": user.phone_no or "",
        "user_city": user.city or "",
        "user_country": user.country or "",
        "user_bio": user.bio or "",
        "group_name": group_info,
        "log_year": log_year,
        "log_year_section": log_year_section,
        "group_full_info": group_full_info,
        # Statistics
        "logs_count": logs_count,
        "approved_count": approved_count,
        "pending_count": pending_count,
        "departments_count": departments_count,
    }

    return render(request, "student_profile.html", data)


# edit profile contact
@login_required
def update_contact_info(request):
    if request.method == "POST":
        phone = request.POST.get("phone", "")
        city = request.POST.get("city", "")
        country = request.POST.get("country", "")

        try:
            # Update user profile info with transaction to ensure data consistency
            with transaction.atomic():
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
                    "user_phone": phone,
                    "user_city": city,
                    "user_country": country,
                }
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method"})


# edit profile bio
@login_required
def update_biography(request):
    if request.method == "POST":
        biography = request.POST.get("biography", "")

        try:
            # Update user biography with transaction to ensure data consistency
            with transaction.atomic():
                user = request.user
                user.bio = biography
                user.save()

                # Update session data
                request.session["bio"] = biography
                request.session.modified = True

            return JsonResponse({"success": True, "user_bio": biography})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request method"})


# Update profile photo
@login_required
def update_profile_photo(request):
    if request.method == "POST" and request.FILES.get("profile_photo"):
        try:
            with transaction.atomic():
                user = request.user

                # Delete old profile photo if it exists
                if user.profile_photo and hasattr(user.profile_photo, "path"):
                    try:
                        if os.path.exists(user.profile_photo.path) and not user.profile_photo.path.endswith('default.jpg'):
                            os.remove(user.profile_photo.path)
                    except Exception as e:
                        print(f"Error deleting old profile photo: {e}")

                # Save new profile photo
                user.profile_photo = request.FILES["profile_photo"]
                user.save()

                return JsonResponse({"success": True, "profile_photo": user.profile_photo.url})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "No photo provided or invalid request"})


@login_required
def student_final_records(request):
    # Get the current student
    student = request.user.student

    # Get filter parameters
    department_id = request.GET.get('department')
    activity_type_id = request.GET.get('activity_type')
    review_status = request.GET.get('status', 'pending')
    search_query = request.GET.get('q', '').strip()

    # Base queryset - filter by student and use select_related to reduce database queries
    logs = StudentLogFormModel.objects.filter(student=student).select_related(
        'department', 'activity_type', 'core_diagnosis', 'tutor', 'tutor__user'
    )

    # Filter by review status if specified
    if review_status == 'pending':
        logs = logs.filter(is_reviewed=False)
    elif review_status == 'reviewed':
        logs = logs.filter(is_reviewed=True)
    # If 'all' is selected, don't apply any filter

    # Apply filters if provided
    if department_id:
        logs = logs.filter(department_id=department_id)

    if activity_type_id:
        logs = logs.filter(activity_type_id=activity_type_id)

    if search_query:
        logs = logs.filter(
            models.Q(description__icontains=search_query) |
            models.Q(patient_id__icontains=search_query) |
            models.Q(core_diagnosis__name__icontains=search_query)
        )

    # Order by most recent first
    logs = logs.order_by('-date', '-created_at')

    # Pagination
    paginator = Paginator(logs, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get departments and activity types for filters - use select_related to reduce queries
    departments = Department.objects.filter(
        log_year_section=student.group.log_year_section
    ).distinct().order_by('name')

    # Only fetch activity types if needed
    if department_id:
        activity_types = ActivityType.objects.filter(
            department_id=department_id
        ).order_by('name')
    else:
        activity_types = ActivityType.objects.none()

    # Student info for PDF
    student_info = {
        "student_name": student.user.get_full_name(),
        "student_id": student.student_id,
        "year_name": student.group.log_year.year_name if student.group else "",
        "section_name": student.group.log_year_section.year_section_name if student.group else "",
        "group_name": student.group.group_name if student.group else "",
    }

    context = {
        'logs': page_obj,
        'departments': departments,
        'activity_types': activity_types,
        'selected_department': department_id,
        'selected_activity_type': activity_type_id,
        'selected_status': review_status,
        'search_query': search_query,
        'student_info': student_info,
    }

    return render(request, "student_final_records.html", context)





@login_required
def get_student_info(request):
    student = request.user.student
    context = {
        "student_name": f"{student.user.first_name} {student.user.last_name}",
        "student_id": student.student_id,
        "year_name": (
            student.group.log_year.year_name
            if student.group and student.group.log_year
            else ""
        ),
        "section_name": (
            student.group.log_year_section.year_section_name
            if student.group and student.group.log_year_section
            else ""
        ),
        "group_name": student.group.group_name if student.group else "",
    }
    html = render_to_string("components/student_info.html", context)
    return HttpResponse(html)


@login_required
def get_departments_by_year(request):
    try:
        student = request.user.student
        log_year = student.group.log_year if student.group else None

        if log_year:
            departments = (
                Department.objects.filter(log_year=log_year).distinct().order_by("name")
            )
            # Prepare concatenated data
            department_data = [
                {
                    "id": dept.id,
                    "name": (
                        f"{dept.name} - {dept.log_year.log_year_section.name}"
                        if dept.log_year.log_year_section
                        else dept.name
                    ),
                }
                for dept in departments
            ]
            return JsonResponse(department_data, safe=False)
        else:
            return JsonResponse([], safe=False)
    except Exception as e:
        print(f"Error in get_departments_by_year: {e}")
        return JsonResponse([], safe=False)


@login_required
def get_activity_types(request):
    department_id = request.GET.get("department")
    if not department_id:
        print("No department_id provided in get_activity_types")  # Debug
        return JsonResponse([], safe=False)

    student = request.user.student
    log_year_section = student.group.log_year_section if student.group else None
    print(f"Student: {student}, Log Year Section: {log_year_section}")  # Debug

    activity_types = (
        ActivityType.objects.filter(
            department_id=department_id, department__log_year_section=log_year_section
        )
        .distinct()
        .order_by("name")
    )

    print(
        f"Activity Types for department {department_id}: {list(activity_types)}"
    )  # Debug

    activity_type_data = [
        {"id": activity.id, "name": activity.name} for activity in activity_types
    ]
    return JsonResponse(activity_type_data, safe=False)


@login_required
def get_core_diagnosis(request):
    activity_type_id = request.GET.get("activity_type")
    if not activity_type_id:
        return JsonResponse([], safe=False)

    core_diagnoses = (
        CoreDiaProSession.objects.filter(activity_type_id=activity_type_id)
        .distinct()
        .order_by("name")
    )

    core_diagnosis_data = [
        {"id": core.id, "name": core.name} for core in core_diagnoses
    ]
    return JsonResponse(core_diagnosis_data, safe=False)


@login_required
def get_tutors(request):
    department_id = request.GET.get("department")
    if not department_id:
        return JsonResponse([], safe=False)

    tutors = (
        Doctor.objects.filter(departments=department_id)
        .distinct()
        .order_by("user__first_name")
    )

    tutor_data = [
        {"id": tutor.id, "name": f"{tutor.user.get_full_name()}"} for tutor in tutors
    ]
    return JsonResponse(tutor_data, safe=False)


@login_required
def get_date_restrictions(request):
    """API endpoint to get date restriction settings for students"""
    try:
        # Get date restriction settings or create default if none exist
        settings = DateRestrictionSettings.objects.first()
        if not settings:
            settings = DateRestrictionSettings.objects.create(
                past_days_limit=7,
                allow_future_dates=False,
                future_days_limit=0
            )

        # Get current day of week (0=Monday, 6=Sunday)
        current_day = timezone.now().weekday()

        # Get allowed days from session or use default
        allowed_days_str = request.session.get('allowed_days_for_students', '0,1,2,3,4,5,6')
        allowed_days = [int(day) for day in allowed_days_str.split(',') if day.strip()]

        # Get active status from session or use default
        is_active = request.session.get('date_restrictions_active', True)

        # Return settings as JSON
        data = {
            "pastDaysLimit": settings.past_days_limit,
            "allowFutureDates": settings.allow_future_dates,
            "futureDaysLimit": settings.future_days_limit,
            "isCurrentDayAllowed": current_day in allowed_days,
            "allowedDays": allowed_days,
            "isActive": is_active
        }
        return JsonResponse(data)
    except Exception as e:
        # Return default settings in case of error
        return JsonResponse({
            "pastDaysLimit": 7,
            "allowFutureDates": False,
            "futureDaysLimit": 0,
            "isCurrentDayAllowed": True,
            "allowedDays": [0, 1, 2, 3, 4, 5, 6],
            "isActive": True,
            "error": str(e)
        })


@login_required
def generate_records_pdf(request):
    # Get the current student
    student = request.user.student

    # Get filter parameters (same as in student_final_records)
    department_id = request.GET.get('department')
    activity_type_id = request.GET.get('activity_type')
    review_status = request.GET.get('status', 'pending')
    search_query = request.GET.get('q', '').strip()

    # Base queryset - filter by student
    logs = StudentLogFormModel.objects.filter(student=student)

    # Filter by review status if specified
    if review_status == 'pending':
        logs = logs.filter(is_reviewed=False)
    elif review_status == 'reviewed':
        logs = logs.filter(is_reviewed=True)
    # If 'all' is selected, don't apply any filter

    # Apply filters if provided
    if department_id:
        logs = logs.filter(department_id=department_id)

    if activity_type_id:
        logs = logs.filter(activity_type_id=activity_type_id)

    if search_query:
        logs = logs.filter(
            models.Q(description__icontains=search_query) |
            models.Q(patient_id__icontains=search_query) |
            models.Q(core_diagnosis__name__icontains=search_query)
        )

    # Order by most recent first
    logs = logs.order_by('-date', '-created_at')

    # Student info for PDF
    student_info = {
        "student_name": student.user.get_full_name(),
        "student_id": student.student_id,
        "year_name": student.group.log_year.year_name if student.group else "",
        "section_name": student.group.log_year_section.year_section_name if student.group else "",
        "group_name": student.group.group_name if student.group else "",
    }

    # Create context for PDF template
    context = {
        'logs': logs,
        'student_info': student_info,
        'generated_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'status_type': review_status,
    }

    # Render HTML content
    html_string = render_to_string('student_records_pdf.html', context)

    # Create HTTP response with PDF
    response = HttpResponse(content_type='application/pdf')

    # Create a filename that reflects the status
    if review_status == 'pending':
        status_text = 'pending'
    elif review_status == 'reviewed':
        status_text = 'reviewed'
    else:
        status_text = 'all'

    response['Content-Disposition'] = f'attachment; filename="student_records_{student.student_id}_{status_text}.pdf"'

    # Generate PDF
    pisa_status = pisa.CreatePDF(html_string, dest=response)

    # Return PDF response if successful
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)

    return response


@login_required
def delete_support_ticket(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id, student=request.user.student)
    if ticket.status == 'pending':  # Only allow deletion of pending tickets
        ticket.delete()
        messages.success(request, "Support ticket deleted successfully.")
    else:
        messages.error(request, "Cannot delete a ticket that has been resolved.")
    return redirect('student_section:student_support')


@login_required
def edit_log(request, log_id):
    # Get the log entry and verify it belongs to the current student
    log = get_object_or_404(StudentLogFormModel, id=log_id, student=request.user.student)

    # Check if the log has already been reviewed - if so, don't allow editing
    if log.is_reviewed:
        messages.error(request, "You cannot edit logs that have already been reviewed.")
        return redirect('student_section:student_final_records')

    if request.method == "POST":
        form = StudentLogFormModelForm(request.POST, instance=log, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Log entry updated successfully.")
            return redirect('student_section:student_final_records')
    else:
        form = StudentLogFormModelForm(instance=log, user=request.user)

    student = request.user.student
    context = {
        "form": form,
        "student_name": student.user.get_full_name(),
        "student_id": student.student_id,
        "year_name": student.group.log_year.year_name if student.group else "",
        "section_name": student.group.log_year_section.year_section_name if student.group else "",
        "group_name": student.group.group_name if student.group else "",
        "is_edit": True,
        "log": log,
    }
    return render(request, "student_edit_log.html", context)


@login_required
def delete_log(request, log_id):
    # Get the log entry and verify it belongs to the current student
    log = get_object_or_404(StudentLogFormModel, id=log_id, student=request.user.student)

    # Check if the log has already been reviewed - if so, don't allow deletion
    if log.is_reviewed:
        messages.error(request, "You cannot delete logs that have already been reviewed.")
        return redirect('student_section:student_final_records')

    if request.method == "POST":
        log.delete()
        messages.success(request, "Log entry deleted successfully.")
        return redirect('student_section:student_final_records')

    # If it's not a POST request, redirect to the records page
    return redirect('student_section:student_final_records')


@login_required
def notifications(request):
    student = request.user.student

    # Get all notifications for this student
    notifications_list = StudentNotification.objects.filter(recipient=student).order_by('-created_at')

    # Mark notifications as read if requested
    if request.GET.get('mark_read'):
        notification_id = request.GET.get('mark_read')
        notification = get_object_or_404(StudentNotification, id=notification_id, recipient=student)
        notification.mark_as_read()
        return redirect('student_section:notifications')

    # Mark all as read if requested
    if request.GET.get('mark_all_read'):
        notifications_list.filter(is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('student_section:notifications')

    # Pagination
    paginator = Paginator(notifications_list, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'notifications': page_obj,
        'unread_count': notifications_list.filter(is_read=False).count(),
    }

    return render(request, "student_notifications.html", context)


@login_required
def get_log_details(request, log_id):
    """API endpoint to get details for a specific log entry"""
    try:
        # Get the log entry and verify it belongs to the current student
        log = get_object_or_404(StudentLogFormModel, id=log_id, student=request.user.student)

        # Format the data for the response
        data = {
            "basic_info": {
                "date": log.date.strftime("%Y-%m-%d"),
                "department": log.department.name,
                "activity_type": log.activity_type.name,
                "core_diagnosis": log.core_diagnosis.name,
                "tutor": log.tutor.user.get_full_name(),
                "training_site": log.training_site.name if hasattr(log, 'training_site') and log.training_site else "N/A",
                "status": "Reviewed" if log.is_reviewed else "Pending",
                "is_approved": not (log.reviewer_comments and log.reviewer_comments.startswith("REJECTED")) if log.is_reviewed else None,
            },
            "patient_info": {
                "patient_id": log.patient_id if log.patient_id else "N/A",
                "age": log.patient_age if hasattr(log, 'patient_age') and log.patient_age else "N/A",
                "gender": log.patient_gender if hasattr(log, 'patient_gender') and log.patient_gender else "N/A",
            },
            "description": log.description if log.description else "",
            "reviewer_comments": log.reviewer_comments if log.is_reviewed and log.reviewer_comments else "",
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
            "updated_at": log.updated_at.strftime("%Y-%m-%d %H:%M:%S") if log.updated_at else "",
            "review_date": log.review_date.strftime("%Y-%m-%d %H:%M:%S") if log.review_date else None,
        }
        return JsonResponse(data)
    except StudentLogFormModel.DoesNotExist:
        return JsonResponse({"error": "Log entry not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
