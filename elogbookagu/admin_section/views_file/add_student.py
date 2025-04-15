from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.hashers import make_password
from django.db import transaction
import csv
import io
from accounts.models import CustomUser, Student
from admin_section.models import Group
from admin_section.forms import StudentForm, StudentUserForm, BulkStudentUploadForm, AssignStudentToGroupForm


def add_student(request):
    # Initialize forms
    user_form = StudentUserForm()
    student_form = StudentForm()
    bulk_form = BulkStudentUploadForm()
    assign_form = AssignStudentToGroupForm()
    bulk_results = None

    # Handle form submissions
    if request.method == 'POST':
        # Check which form was submitted
        if 'add_student' in request.POST:
            # Individual student addition
            user_form = StudentUserForm(request.POST)
            student_form = StudentForm(request.POST)

            if user_form.is_valid() and student_form.is_valid():
                try:
                    with transaction.atomic():
                        # Create user with student role
                        user = user_form.save(commit=False)
                        user.role = 'student'
                        user.save()

                        # Create student profile
                        student = student_form.save(commit=False)
                        student.user = user
                        student.save()

                        messages.success(request, f'Student {user.first_name} {user.last_name} added successfully!')
                        return redirect('admin_section:add_student')
                except Exception as e:
                    messages.error(request, f'Error adding student: {str(e)}')

        elif 'bulk_upload' in request.POST:
            bulk_form = BulkStudentUploadForm(request.POST, request.FILES)
            if bulk_form.is_valid():
                csv_file = request.FILES['csv_file']
                group = bulk_form.cleaned_data['group']
                
                # Validate file size (5MB limit)
                if csv_file.size > 5 * 1024 * 1024:
                    messages.error(request, 'File size must be less than 5MB')
                    return redirect('admin_section:add_student')

                try:
                    decoded_file = csv_file.read().decode('utf-8')
                except UnicodeDecodeError:
                    messages.error(request, 'Please upload a valid CSV file')
                    return redirect('admin_section:add_student')

                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                
                required_fields = ['username', 'email', 'password', 'first_name', 
                                 'last_name', 'student_id', 'phone_no', 'city', 'country']
                
                # Validate CSV headers
                headers = reader.fieldnames
                if not headers or not all(field in headers for field in required_fields):
                    messages.error(request, 'CSV file must contain all required fields')
                    return redirect('admin_section:add_student')

                success_count = 0
                error_count = 0
                error_messages = []

                for row in reader:
                    try:
                        with transaction.atomic():
                            # Validate student_id
                            student_id = row.get('student_id', '').strip()
                            if not student_id:
                                raise ValueError("Student ID is required")
                            if Student.objects.filter(student_id=student_id).exists():
                                raise ValueError(f"Student ID '{student_id}' already exists")

                            # Create user
                            user = CustomUser.objects.create(
                                username=row['username'].strip(),
                                email=row['email'].strip(),
                                password=make_password(row['password'].strip()),
                                first_name=row['first_name'].strip(),
                                last_name=row['last_name'].strip(),
                                phone_no=row['phone_no'].strip(),
                                city=row['city'].strip(),
                                country=row['country'].strip(),
                                role='student'
                            )

                            # Create student profile with group
                            Student.objects.create(
                                user=user,
                                student_id=student_id,
                                group=group
                            )

                            success_count += 1
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f"Row {reader.line_num}: {str(e)}")

                # Prepare results
                bulk_results = {
                    'success_count': success_count,
                    'error_count': error_count,
                    'error_messages': error_messages[:10],
                    'total_errors': len(error_messages)
                }

                if success_count > 0:
                    messages.success(request, f"Successfully added {success_count} students to {group}.")
                if error_count > 0:
                    messages.warning(request, f"Failed to add {error_count} students. See details below.")

        elif 'assign_student' in request.POST:
            # Assign existing student to group
            assign_form = AssignStudentToGroupForm(request.POST)
            if assign_form.is_valid():
                student = assign_form.cleaned_data['student']
                group = assign_form.cleaned_data['group']

                student.group = group
                student.save()

                messages.success(request, f'Student {student.user.first_name} {student.user.last_name} assigned to {group} successfully!')
                return redirect('admin_section:add_student')

    # Get students for the table
    search_query = request.GET.get('q', '').strip()
    group_filter = request.GET.get('group')

    # Base queryset
    students = Student.objects.select_related('user', 'group').all()

    # Apply filters
    if group_filter:
        students = students.filter(group_id=group_filter)

    if search_query:
        students = students.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(student_id__icontains=search_query)
        )

    # Order students
    students = students.order_by('user__last_name', 'user__first_name')

    # Pagination
    paginator = Paginator(students, 10)  # Show 10 students per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all groups for filtering
    groups = Group.objects.all().order_by('log_year_section__year_section_name', 'group_name')

    # Prepare sample CSV data
    sample_csv_data = {
        'username': 'john.doe',
        'email': 'john.doe@example.com',
        'password': 'securepassword123',
        'first_name': 'John',
        'last_name': 'Doe',
        'student_id': 'STU12345',
        'phone_no': '1234567890',
        'city': 'New York',
        'country': 'USA'
    }

    context = {
        'user_form': user_form,
        'student_form': student_form,
        'bulk_form': bulk_form,
        'assign_form': assign_form,
        'students': page_obj,
        'groups': groups,
        'selected_group': group_filter,
        'search_query': search_query,
        'bulk_results': bulk_results,
        'sample_csv_data': sample_csv_data
    }

    return render(request, "admin_section/add_student.html", context)


def remove_from_group(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    group_name = student.group.group_name if student.group else 'No Group'

    student.group = None
    student.save()

    messages.success(request, f'Student {student.user.first_name} {student.user.last_name} removed from {group_name} successfully!')
    return redirect('admin_section:add_student')


def download_sample_csv(request):
    """Download a sample CSV file for student import"""
    import csv
    from django.http import HttpResponse

    # Create the response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sample_student_import.csv"'

    # Create the CSV writer
    writer = csv.writer(response)

    # Write the header row
    headers = ['username', 'email', 'password', 'first_name', 'last_name', 'student_id', 'phone_no', 'city', 'country']
    writer.writerow(headers)

    # Write a sample data row
    sample_data = {
        'username': 'john.doe',
        'email': 'john.doe@example.com',
        'password': 'securepassword123',
        'first_name': 'John',
        'last_name': 'Doe',
        'student_id': 'STU12345',
        'phone_no': '1234567890',
        'city': 'New York',
        'country': 'USA'
    }
    writer.writerow([sample_data.get(header, '') for header in headers])

    return response
