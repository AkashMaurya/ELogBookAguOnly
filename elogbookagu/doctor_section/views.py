from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from accounts.models import Doctor
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models, transaction
from django.utils import timezone
from datetime import datetime, timedelta
import os
import json
from .models import DoctorSupportTicket
from .forms import DoctorSupportTicketForm, LogReviewForm, BatchReviewForm
from student_section.models import StudentLogFormModel


@login_required
def doctor_dash(request):
    doctor = request.user

    try:
        # Fetch dashboard data
        total_records = StudentRecord.objects.filter(assigned_doctor=doctor).count()
        reviewed = StudentRecord.objects.filter(
            assigned_doctor=doctor, is_reviewed=True
        ).count()
        left_to_review = total_records - reviewed if total_records > 0 else 0

        # Priority records
        priority_threshold = datetime.now() + timedelta(days=3)
        priority_records = StudentRecord.objects.filter(
            assigned_doctor=doctor, is_reviewed=False, due_date__lte=priority_threshold
        ).order_by("due_date")[:5]

    except Exception as e:
        # Handle potential errors (e.g., database issues)
        total_records = 0
        reviewed = 0
        left_to_review = 0
        priority_records = []
        print(f"Error fetching dashboard data: {e}")

    context = {
        "total_records": total_records,
        "left_to_review": left_to_review,
        "reviewed": reviewed,
        "priority_records": priority_records,
        "request": request,
    }

    return render(request, "doctor_dash.html", context)


@login_required
def doctor_profile(request):
    # Get the currently logged-in user from the request
    user = request.user  # ✅ Ensure user object is available

    # Get the profile photo URL correctly
    if user.profile_photo:  # ✅ Check if user has a profile photo
        profile_photo = user.profile_photo.url
    else:
        profile_photo = (
            "/media/profiles/default.jpg"  # Default image if no profile photo
        )

    # get Doctor Profile
    doctor = getattr(
        user, "doctor_profile", None
    )  # `related_name="doctor_profile"` से doctor प्राप्त करें

    # Get doctor's departments
    if doctor:
        doctor_departments = ", ".join(
            dept.name for dept in doctor.departments.all()
        )  # ✅ स्ट्रिंग में बदलें
    else:
        doctor_departments = (
            None  # ❌ Empty string ना रखें, ताकि `{% if doctor_departments %}` सही से चले
        )

    # Fetch other session data (making sure these values exist in session)
    username = request.session.get("username", "Guest").upper()
    first_name = request.session.get("first_name", "GuestFirstName").upper()
    last_name = request.session.get("last_name", "GuestLastName").upper()
    full_name = f"{first_name} {last_name}"  # Combine first and last name
    user_role = request.session.get("role", "guest").upper()  # Get the user's role
    user_city = request.session.get("city", "")  # User's city, default is empty
    user_country = request.session.get(
        "country", ""
    )  # User's country, default is empty
    user_phone = request.session.get("phone_no", "")  # User's phone, default is empty
    user_bio = request.session.get("bio", "")  # User's bio, default is empty
    user_speciality = request.session.get(
        "speciality", ""
    )  # User's speciality, default is empty
    user_email = request.session.get("email", "abc@example.com")  # User's email

    # List of editable fields, can be used for form rendering
    editable_fields = [
        "password",
        "profile_photo",
        "city",
        "country",
        "phone",
        "bio",
        "speciality",
    ]

    # Prepare the context dictionary with all the necessary data to render the template
    data = {
        "username": username,
        "full_name": full_name,
        "profile_photo": profile_photo,  # ✅ Now using user.profile_photo.url
        "user_role": user_role,
        "first_name": first_name,
        "last_name": last_name,
        "user_city": user_city,
        "user_country": user_country,
        "user_phone": user_phone,
        "user_bio": user_bio,
        "user_speciality": user_speciality,
        "user_email": user_email,
        "editable_fields": editable_fields,  # List of fields that can be edited
        "doctor_departments": doctor_departments,
    }

    # Debugging to check the profile photo URL
    print(f"Profile Photo URL: {profile_photo}")  # For debugging, can be removed later
    print(f"Doctor Departments: {doctor_departments}")
    # Render the template with the context data
    return render(request, "doctor_profile.html", data)


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
                    "user_phone": phone,
                    "user_city": city,
                    "user_country": country,
                }
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def update_profile_photo(request):
    if request.method == "POST" and request.FILES.get("profile_photo"):
        user = request.user
        # Delete old profile photo if it exists
        if user.profile_photo and hasattr(user.profile_photo, "path"):
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
def doctor_blogs(request):
    return render(request, "doctor_blogs.html")


@login_required
def doctor_help(request):
    if request.method == "POST":
        form = DoctorSupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.doctor = request.user.doctor_profile
            ticket.save()
            messages.success(request, "Support ticket submitted successfully. We will respond to your issue soon.")
            return redirect("doctor_section:doctor_help")
    else:
        form = DoctorSupportTicketForm()

    # Get all tickets for the current doctor
    tickets = DoctorSupportTicket.objects.filter(doctor=request.user.doctor_profile).order_by('-date_created')

    context = {
        "form": form,
        "tickets": tickets,
    }
    return render(request, "doctor_help.html", context)


@login_required
def doctor_reviews(request):
    doctor = request.user.doctor_profile

    # Get filter parameters
    department_id = request.GET.get('department')
    status = request.GET.get('status', 'pending')
    search_query = request.GET.get('q', '').strip()

    # Get departments associated with this doctor
    doctor_departments = doctor.departments.all()

    # Base queryset - filter by departments the doctor is associated with
    logs = StudentLogFormModel.objects.filter(department__in=doctor_departments)

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
        'departments': doctor_departments,
        'selected_department': department_id,
        'selected_status': status,
        'search_query': search_query,
        'batch_form': batch_form,
    }

    return render(request, "doctor_reviews.html", context)


def logout(request):
    auth_logout(request)
    # Clear the session username
    request.session.pop("username", None)
    return redirect("login")


@login_required
def delete_support_ticket(request, ticket_id):
    ticket = get_object_or_404(DoctorSupportTicket, id=ticket_id, doctor=request.user.doctor_profile)
    if ticket.status == 'pending':  # Only allow deletion of pending tickets
        ticket.delete()
        messages.success(request, "Support ticket deleted successfully.")
    else:
        messages.error(request, "Cannot delete a ticket that has been resolved.")
    return redirect('doctor_section:doctor_help')


@login_required
def review_log(request, log_id):
    # Get the doctor and the log
    doctor = request.user.doctor_profile
    log = get_object_or_404(StudentLogFormModel, id=log_id)

    # Check if the doctor is associated with the log's department
    if log.department not in doctor.departments.all():
        messages.error(request, "You don't have permission to review this log.")
        return redirect('doctor_section:doctor_reviews')

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
            return redirect('doctor_section:doctor_reviews')
    else:
        form = LogReviewForm(instance=log)

    context = {
        'form': form,
        'log': log,
    }

    return render(request, 'doctor_review_log.html', context)


@login_required
def batch_review(request):
    if request.method != 'POST':
        return redirect('doctor_section:doctor_reviews')

    form = BatchReviewForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid form submission.")
        return redirect('doctor_section:doctor_reviews')

    # Get form data
    log_ids = form.cleaned_data['log_ids'].split(',')
    action = form.cleaned_data['action']
    comments = form.cleaned_data['comments']

    # Get the doctor
    doctor = request.user.doctor_profile
    doctor_departments = doctor.departments.all()

    # Get logs that belong to the doctor's departments
    logs = StudentLogFormModel.objects.filter(
        id__in=log_ids,
        department__in=doctor_departments
    )

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
    return redirect('doctor_section:doctor_reviews')
