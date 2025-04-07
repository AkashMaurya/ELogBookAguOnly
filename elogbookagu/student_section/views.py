from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from .forms import StudentLogFormModelForm
from .models import StudentLogFormModel
from admin_section.models import ActivityType, CoreDiaProSession, LogYear
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
    return render(request, "student_support.html")


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
    return render(request, "student_final_records.html")


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
