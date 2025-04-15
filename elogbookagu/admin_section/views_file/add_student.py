from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
import csv
from ..forms import (
    StudentUserForm,
    StudentForm,
    BulkUserUploadForm,  # Changed from BulkUploadForm
    AssignStudentForm
)
from accounts.models import Student
from ..models import Group
from django.contrib.auth import get_user_model

CustomUser = get_user_model()


@login_required
def add_student(request):
    # Initialize forms
    user_form = StudentUserForm()
    student_form = StudentForm()
    bulk_form = BulkUserUploadForm()  # Changed from BulkUploadForm
    assign_form = AssignStudentForm()

    # Get search parameters
    search_query = request.GET.get("q", "")
    selected_group = request.GET.get("group", "")
    page_number = request.GET.get("page", 1)

    # Base queryset
    students = Student.objects.select_related("user", "group").all()

    # Apply filters
    if search_query:
        students = students.filter(
            Q(student_id__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
        )

    if selected_group:
        students = students.filter(group_id=selected_group)

    # Pagination
    paginator = Paginator(students, 10)  # Show 10 students per page
    page_obj = paginator.get_page(page_number)

    # Get all groups for the filter dropdown
    groups = Group.objects.all()

    # Handle form submissions
    if request.method == "POST":
        if "add_student" in request.POST:
            # Individual student addition
            user_form = StudentUserForm(request.POST)
            student_form = StudentForm(request.POST)

            if user_form.is_valid() and student_form.is_valid():
                try:
                    with transaction.atomic():
                        # Create user with student role
                        user = user_form.save(commit=False)
                        user.role = "student"
                        user.save()

                        # Create student profile
                        student = student_form.save(commit=False)
                        student.user = user
                        student.save()

                        messages.success(
                            request,
                            f"Student {user.first_name} {user.last_name} added successfully!",
                        )
                        return redirect("admin_section:add_student")
                except Exception as e:
                    messages.error(request, f"Error adding student: {str(e)}")

        elif "bulk_upload" in request.POST:
            bulk_form = BulkUserUploadForm(request.POST, request.FILES)  # Changed from BulkUploadForm
            if bulk_form.is_valid():
                try:
                    # Process the CSV file here
                    # Add your bulk upload logic
                    messages.success(request, "Bulk upload completed successfully!")
                except Exception as e:
                    messages.error(request, f"Error during bulk upload: {str(e)}")

        elif "assign_student" in request.POST:
            assign_form = AssignStudentForm(request.POST)
            if assign_form.is_valid():
                try:
                    student = assign_form.cleaned_data["student"]
                    group = assign_form.cleaned_data["group"]
                    student.group = group
                    student.save()
                    messages.success(
                        request, f"Student successfully assigned to {group.group_name}"
                    )
                except Exception as e:
                    messages.error(
                        request, f"Error assigning student to group: {str(e)}"
                    )

    context = {
        "user_form": user_form,
        "student_form": student_form,
        "bulk_form": bulk_form,
        "assign_form": assign_form,
        "students": page_obj,
        "groups": groups,
        "selected_group": selected_group,
        "search_query": search_query,
    }

    return render(request, "admin_section/add_student.html", context)


@login_required
def remove_from_group(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
        group_name = student.group.group_name if student.group else "No group"
        student.group = None
        student.save()
        messages.success(request, f'Student removed from {group_name} successfully!')
    except Student.DoesNotExist:
        messages.error(request, 'Student not found!')
    except Exception as e:
        messages.error(request, f'Error removing student from group: {str(e)}')

    return redirect('admin_section:add_student')


@login_required
def download_sample_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_students.csv"'

    writer = csv.writer(response)
    writer.writerow(['username', 'email', 'password', 'first_name', 'last_name', 'student_id', 'group', 'phone_no', 'city', 'country'])

    # Add sample data rows
    writer.writerow(['student1', 'student1@example.com', 'SecurePass123', 'John', 'Doe', 'STU12345', 'B1', '1234567890', 'New York', 'USA'])
    writer.writerow(['student2', 'student2@example.com', 'SecurePass456', 'Jane', 'Smith', 'STU67890', 'A2', '9876543210', 'London', 'UK'])
    writer.writerow(['student3', 'student3@example.com', 'SecurePass789', 'Alex', 'Johnson', 'STU24680', 'B2', '5555555555', 'Paris', 'France'])
    writer.writerow(['student4', 'student4@example.com', 'SecurePass101', 'Maria', 'Garcia', 'STU13579', 'A1', '6666666666', 'Berlin', 'Germany'])

    return response
