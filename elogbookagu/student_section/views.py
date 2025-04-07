from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db import models
from django.template.loader import render_to_string
from datetime import datetime
from xhtml2pdf import pisa
from .forms import StudentLogFormModelForm, SupportTicketForm
from .models import StudentLogFormModel, SupportTicket
from admin_section.models import ActivityType, CoreDiaProSession, LogYear, Department
from accounts.models import Doctor, Student
from django.contrib import messages

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


@login_required
def student_blogs(request):
    return render(request, "student_blogs.html")


@login_required
def student_support(request):
    if request.method == "POST":
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.student = request.user.student
            ticket.save()
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


@login_required
def student_elog(request):
    if request.method == "POST":
        form = StudentLogFormModelForm(request.POST, user=request.user)
        if form.is_valid():
            log_entry = form.save(commit=False)
            log_entry.student = request.user.student
            log_entry.log_year = request.user.student.group.log_year
            log_entry.log_year_section = request.user.student.group.log_year_section
            log_entry.group = request.user.student.group
            log_entry.save()
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
    # getting the User
    user = request.user
    print(
        "Current User:", user.email, "Role:", getattr(user, "role", None)
    )  # Debug print

    # getting the user photo
    if user.profile_photo:
        profile_photo = user.profile_photo.url
    else:
        profile_photo = "/media/profiles/default.jpg"

    # get Student Profile with related group data using select_related
    try:
        student = Student.objects.select_related(
            "group", "group__log_year", "group__log_year_section"
        ).get(user=user)
        print("Found student:", student)  # Debug print
        print("Student Group:", getattr(student, "group", None))  # Debug print
    except Student.DoesNotExist:
        student = None
        print("No student profile found for user:", user.email)

    # Initialize variables
    group_info = None
    log_year = None
    log_year_section = None
    group_full_info = None

    # Get group information if student exists and has a group
    if student and student.group:
        group = student.group
        print(
            "Group details:",
            {  # Debug print
                "name": group.group_name,
                "log_year": getattr(group.log_year, "year_name", None),
                "section": getattr(group.log_year_section, "year_section_name", None),
            },
        )

        group_info = group.group_name
        log_year = group.log_year.year_name if group.log_year else None
        log_year_section = (
            group.log_year_section.year_section_name if group.log_year_section else None
        )
        group_full_info = str(group)

    data = {
        "profile_photo": profile_photo,
        "full_name": f"{user.first_name} {user.last_name}",
        "user_email": user.email,
        "user_phone": user.phone_no,
        "user_city": user.city,
        "user_country": user.country,
        "user_bio": user.bio if hasattr(user, "bio") else "",
        "group_name": group_info,
        "log_year": log_year,
        "log_year_section": log_year_section,
        "group_full_info": group_full_info,
    }

    print(
        "Final data being sent to template:",
        {  # Debug print
            "group_name": data["group_name"],
            "log_year": data["log_year"],
            "log_year_section": data["log_year_section"],
            "group_full_info": data["group_full_info"],
        },
    )

    return render(request, "student_profile.html", data)


# edit profile contact
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


# edit profile bio
@login_required
def update_biography(request):
    if request.method == "POST":
        biography = request.POST.get("biography")

        try:
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


@login_required
def student_final_records(request):
    # Get the current student
    student = request.user.student

    # Get filter parameters
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

    # Pagination
    paginator = Paginator(logs, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get departments and activity types for filters
    departments = Department.objects.filter(
        log_year_section=student.group.log_year_section
    ).distinct().order_by('name')

    activity_types = ActivityType.objects.all().order_by('name')
    if department_id:
        activity_types = activity_types.filter(department_id=department_id)

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
