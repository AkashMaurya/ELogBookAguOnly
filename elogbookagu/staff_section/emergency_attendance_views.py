from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from datetime import date
from .models import StaffEmergencyAttendance
from .forms import EmergencyAttendanceForm, StudentEmergencyAttendanceForm
from accounts.models import Student, Staff
from admin_section.models import Department, TrainingSite, Group


@login_required
def emergency_attendance(request):
    """Main emergency attendance taking view for staff"""
    try:
        staff = request.user.staff_profile
    except Staff.DoesNotExist:
        messages.error(request, "You must be a staff member to access this page.")
        return redirect('staff_section:staff_dash')

    # Check if staff is mapped to any departments
    if not staff.departments.exists():
        messages.warning(request, "You are not mapped to any departments. Please contact the administrator.")
        return redirect('staff_section:staff_dash')

    selected_department = None
    selected_training_site = None
    selected_date = None
    students_data = []

    if request.method == 'POST':
        form = EmergencyAttendanceForm(staff=staff, data=request.POST)
        if form.is_valid():
            department = form.cleaned_data['department']
            training_site = form.cleaned_data['training_site']
            attendance_date = form.cleaned_data['attendance_date']

            # Get students for this department
            students_data = get_students_for_emergency_attendance(staff, department, training_site, attendance_date)
            selected_department = department
            selected_training_site = training_site
            selected_date = attendance_date

            # Process attendance if submitted
            if 'submit_attendance' in request.POST:
                return process_emergency_attendance_submission(
                    request, staff, department, training_site, attendance_date
                )

    else:
        form = EmergencyAttendanceForm(staff=staff)

    context = {
        'form': form,
        'students_data': students_data,
        'selected_department': selected_department,
        'selected_training_site': selected_training_site,
        'selected_date': selected_date,
    }

    return render(request, 'staff_section/emergency_attendance.html', context)


def get_students_for_emergency_attendance(staff, department, training_site, attendance_date):
    """Get students mapped to the staff's department with their attendance status"""
    students_data = []

    # Get all groups that have the same log_year_section as the selected department
    # This is how students are related to departments - through log_year_section
    groups = Group.objects.filter(
        log_year_section=department.log_year_section
    ).select_related('log_year', 'log_year_section')

    # If training site is specified, we could filter further, but for now we'll get all groups
    # in the department's log_year_section

    # Get all students from these groups
    for group in groups:
        for student in group.students.select_related('user').all():
            # Check if emergency attendance already exists for this student on this date
            existing_attendance = StaffEmergencyAttendance.objects.filter(
                student=student,
                department=department,
                date=attendance_date
            ).first()

            student_data = {
                'student': student,
                'group': group,
                'existing_attendance': existing_attendance,
                'form': StudentEmergencyAttendanceForm(instance=existing_attendance) if existing_attendance else StudentEmergencyAttendanceForm()
            }
            students_data.append(student_data)

    return students_data


def process_emergency_attendance_submission(request, staff, department, training_site, attendance_date):
    """Process the emergency attendance form submission"""
    try:
        with transaction.atomic():
            # Get all students for this mapping
            students_data = get_students_for_emergency_attendance(staff, department, training_site, attendance_date)

            attendance_count = 0
            for student_data in students_data:
                student = student_data['student']
                group = student_data['group']

                # Get attendance status from form
                status_key = f'student_{student.id}_status'
                notes_key = f'student_{student.id}_notes'

                status = request.POST.get(status_key)
                notes = request.POST.get(notes_key, '')

                if status in ['present', 'absent']:
                    # Update or create emergency attendance record
                    attendance, created = StaffEmergencyAttendance.objects.update_or_create(
                        student=student,
                        department=department,
                        date=attendance_date,
                        defaults={
                            'staff': staff,
                            'training_site': training_site,
                            'group': group,
                            'status': status,
                            'notes': notes,
                            'is_emergency': True,
                        }
                    )
                    attendance_count += 1

            messages.success(request, f"Emergency attendance recorded successfully for {attendance_count} students.")
            return redirect('staff_section:emergency_attendance_history')

    except Exception as e:
        messages.error(request, f"Error recording emergency attendance: {str(e)}")
        return redirect('staff_section:emergency_attendance')


@login_required
def emergency_attendance_history(request):
    """View emergency attendance history for the staff"""
    try:
        staff = request.user.staff_profile
    except Staff.DoesNotExist:
        messages.error(request, "You must be a staff member to access this page.")
        return redirect('staff_section:staff_dash')

    # Get emergency attendance records marked by this staff
    attendances = StaffEmergencyAttendance.objects.filter(
        staff=staff
    ).select_related(
        'student__user', 'department', 'training_site', 'group'
    ).order_by('-date', '-marked_at')

    # Filter by date if provided
    date_filter = request.GET.get('date')
    if date_filter:
        try:
            filter_date = date.fromisoformat(date_filter)
            attendances = attendances.filter(date=filter_date)
        except ValueError:
            pass

    # Filter by department if provided
    department_filter = request.GET.get('department')
    if department_filter:
        attendances = attendances.filter(department_id=department_filter)

    # Get departments for filter dropdown
    departments = Department.objects.filter(
        staff_members=staff
    ).distinct()

    # Calculate statistics for the filtered attendances
    total_records = attendances.count()
    present_count = attendances.filter(status='present').count()
    absent_count = attendances.filter(status='absent').count()

    context = {
        'attendances': attendances,
        'departments': departments,
        'selected_date': date_filter,
        'selected_department': department_filter,
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count,
    }

    return render(request, 'staff_section/emergency_attendance_history.html', context)


@login_required
def emergency_attendance_summary(request):
    """View emergency attendance summary and statistics"""
    try:
        staff = request.user.staff_profile
    except Staff.DoesNotExist:
        messages.error(request, "You must be a staff member to access this page.")
        return redirect('staff_section:staff_dash')

    # Get summary statistics
    total_attendances = StaffEmergencyAttendance.objects.filter(staff=staff).count()
    present_count = StaffEmergencyAttendance.objects.filter(staff=staff, status='present').count()
    absent_count = StaffEmergencyAttendance.objects.filter(staff=staff, status='absent').count()

    # Get recent attendance by department
    departments_stats = []
    departments = Department.objects.filter(staff_members=staff).distinct()

    for dept in departments:
        dept_attendances = StaffEmergencyAttendance.objects.filter(
            staff=staff,
            department=dept
        )
        dept_stats = {
            'department': dept,
            'total': dept_attendances.count(),
            'present': dept_attendances.filter(status='present').count(),
            'absent': dept_attendances.filter(status='absent').count(),
        }
        departments_stats.append(dept_stats)

    context = {
        'total_attendances': total_attendances,
        'present_count': present_count,
        'absent_count': absent_count,
        'departments_stats': departments_stats,
    }

    return render(request, 'staff_section/emergency_attendance_summary.html', context)


@login_required
def get_students_for_department(request):
    """AJAX endpoint to get students for a selected department"""
    try:
        staff = request.user.staff_profile
    except Staff.DoesNotExist:
        return JsonResponse({'error': 'Not authorized'}, status=403)

    department_id = request.GET.get('department_id')
    training_site_id = request.GET.get('training_site_id')
    
    if not department_id:
        return JsonResponse({'error': 'Department ID required'}, status=400)

    try:
        department = Department.objects.get(id=department_id)
        training_site = None
        if training_site_id:
            training_site = TrainingSite.objects.get(id=training_site_id)

        students_data = get_students_for_emergency_attendance(staff, department, training_site, date.today())

        students_list = []
        for student_data in students_data:
            student = student_data['student']
            group = student_data['group']
            existing_attendance = student_data['existing_attendance']

            students_list.append({
                'id': student.id,
                'name': student.user.get_full_name() or student.user.username,
                'student_id': student.student_id,
                'group': group.group_name,
                'existing_status': existing_attendance.status if existing_attendance else None,
                'existing_notes': existing_attendance.notes if existing_attendance else '',
            })

        return JsonResponse({'students': students_list})

    except Department.DoesNotExist:
        return JsonResponse({'error': 'Department not found'}, status=404)
    except TrainingSite.DoesNotExist:
        return JsonResponse({'error': 'Training site not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
