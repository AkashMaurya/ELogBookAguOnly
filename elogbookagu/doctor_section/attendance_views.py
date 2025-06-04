from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from datetime import date
from .models import StudentAttendance
from .forms import AttendanceForm, StudentAttendanceForm
from accounts.models import Student, Doctor
from admin_section.models import MappedAttendance, TrainingSite, Group


@login_required
def take_attendance(request):
    """Main attendance taking view"""
    # Check if user has doctor role
    if not hasattr(request.user, 'role') or request.user.role != 'doctor':
        messages.error(request, "You must be a doctor to access this page.")
        return redirect('doctor_section:doctor_dash')

    # Check if doctor profile exists
    try:
        doctor = request.user.doctor_profile
    except (Doctor.DoesNotExist, AttributeError):
        messages.error(request, "Doctor profile not found. Please contact the administrator to create your doctor profile.")
        return redirect('doctor_section:doctor_dash')

    # Get mapped training sites for this doctor
    mapped_attendances = MappedAttendance.objects.filter(
        doctors=doctor,
        is_active=True
    ).select_related('training_site').prefetch_related('groups')

    if not mapped_attendances.exists():
        # Check if doctor exists in any mappings (active or inactive)
        all_mappings = MappedAttendance.objects.filter(doctors=doctor)

        if all_mappings.exists():
            inactive_count = all_mappings.filter(is_active=False).count()
            if inactive_count > 0:
                messages.warning(request, f"You have {inactive_count} inactive training site mapping(s). Please contact the administrator to activate them.")
            else:
                messages.warning(request, "Your training site mappings are not active. Please contact the administrator.")
        else:
            messages.warning(request, "You are not mapped to any training sites. Please contact the administrator to create attendance mappings for you.")

        return redirect('doctor_section:doctor_dash')

    selected_training_site = None
    students_data = []
    today = date.today()

    # Handle form processing
    if request.method == 'POST':
        form = AttendanceForm(doctor=doctor, data=request.POST)
        if form.is_valid():
            training_site = form.cleaned_data['training_site']
            attendance_date = form.cleaned_data['attendance_date']
            general_notes = form.cleaned_data['notes']

            # Get students for this training site and doctor mapping
            students_data = get_students_for_attendance(doctor, training_site, attendance_date)
            selected_training_site = training_site

            # Process attendance if submitted
            if 'submit_attendance' in request.POST:
                return process_attendance_submission(request, doctor, training_site, attendance_date, general_notes)
        else:
            # Form has validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = AttendanceForm(doctor=doctor)

    context = {
        'form': form,
        'mapped_attendances': mapped_attendances,
        'students_data': students_data,
        'selected_training_site': selected_training_site,
        'today': today,
    }

    return render(request, 'doctor_section/take_attendance.html', context)


def get_students_for_attendance(doctor, training_site, attendance_date):
    """Get students mapped to the doctor and training site with their attendance status"""
    # Get mapped attendance records for this doctor and training site
    mapped_attendance = MappedAttendance.objects.filter(
        doctors=doctor,
        training_site=training_site,
        is_active=True
    ).prefetch_related('groups__students__user').first()

    if not mapped_attendance:
        return []

    students_data = []
    
    # Get all students from mapped groups
    for group in mapped_attendance.groups.all():
        for student in group.students.select_related('user').all():
            # Check if attendance already exists for this student today
            existing_attendance = StudentAttendance.objects.filter(
                student=student,
                training_site=training_site,
                date=attendance_date
            ).first()

            student_data = {
                'student': student,
                'group': group,
                'existing_attendance': existing_attendance,
                'form': StudentAttendanceForm(instance=existing_attendance) if existing_attendance else StudentAttendanceForm()
            }
            students_data.append(student_data)

    return students_data


def process_attendance_submission(request, doctor, training_site, attendance_date, general_notes):
    """Process the attendance form submission"""
    try:
        with transaction.atomic():
            # Get all students for this mapping
            students_data = get_students_for_attendance(doctor, training_site, attendance_date)
            
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
                    # Update or create attendance record
                    attendance, created = StudentAttendance.objects.update_or_create(
                        student=student,
                        training_site=training_site,
                        date=attendance_date,
                        defaults={
                            'doctor': doctor,
                            'group': group,
                            'status': status,
                            'notes': f"{general_notes}\n{notes}".strip() if general_notes and notes else (general_notes or notes),
                        }
                    )
                    attendance_count += 1

            messages.success(request, f"Attendance recorded successfully for {attendance_count} students.")
            return redirect('doctor_section:attendance_history')

    except Exception as e:
        messages.error(request, f"Error recording attendance: {str(e)}")
        return redirect('doctor_section:take_attendance')


@login_required
def attendance_history(request):
    """View attendance history for the doctor"""
    try:
        doctor = request.user.doctor_profile
    except Doctor.DoesNotExist:
        messages.error(request, "You must be a doctor to access this page.")
        return redirect('doctor_section:doctor_dash')

    # Get attendance records marked by this doctor
    attendances = StudentAttendance.objects.filter(
        doctor=doctor
    ).select_related(
        'student__user', 'training_site', 'group'
    ).order_by('-date', '-marked_at')

    # Filter by date if provided
    date_filter = request.GET.get('date')
    if date_filter:
        try:
            filter_date = date.fromisoformat(date_filter)
            attendances = attendances.filter(date=filter_date)
        except ValueError:
            pass

    # Filter by training site if provided
    training_site_filter = request.GET.get('training_site')
    if training_site_filter:
        attendances = attendances.filter(training_site_id=training_site_filter)

    # Get training sites for filter dropdown
    training_sites = TrainingSite.objects.filter(
        mapped_attendances__doctors=doctor,
        mapped_attendances__is_active=True
    ).distinct()

    # Calculate statistics for the filtered attendances
    total_records = attendances.count()
    present_count = attendances.filter(status='present').count()
    absent_count = attendances.filter(status='absent').count()

    context = {
        'attendances': attendances,
        'training_sites': training_sites,
        'selected_date': date_filter,
        'selected_training_site': training_site_filter,
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count,
    }

    return render(request, 'doctor_section/attendance_history.html', context)


@login_required
def get_students_for_site(request):
    """AJAX endpoint to get students for a selected training site"""
    try:
        doctor = request.user.doctor_profile
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Not authorized'}, status=403)

    training_site_id = request.GET.get('training_site_id')
    if not training_site_id:
        return JsonResponse({'error': 'Training site ID required'}, status=400)

    try:
        training_site = TrainingSite.objects.get(id=training_site_id)
        students_data = get_students_for_attendance(doctor, training_site, date.today())
        
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

    except TrainingSite.DoesNotExist:
        return JsonResponse({'error': 'Training site not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def attendance_summary(request):
    """View attendance summary and statistics"""
    try:
        doctor = request.user.doctor_profile
    except Doctor.DoesNotExist:
        messages.error(request, "You must be a doctor to access this page.")
        return redirect('doctor_section:doctor_dash')

    # Get summary statistics
    total_attendances = StudentAttendance.objects.filter(doctor=doctor).count()
    present_count = StudentAttendance.objects.filter(doctor=doctor, status='present').count()
    absent_count = StudentAttendance.objects.filter(doctor=doctor, status='absent').count()

    # Get recent attendance by training site
    training_sites_stats = []
    training_sites = TrainingSite.objects.filter(
        mapped_attendances__doctors=doctor,
        mapped_attendances__is_active=True
    ).distinct()

    for site in training_sites:
        site_attendances = StudentAttendance.objects.filter(
            doctor=doctor,
            training_site=site
        )
        site_stats = {
            'training_site': site,
            'total': site_attendances.count(),
            'present': site_attendances.filter(status='present').count(),
            'absent': site_attendances.filter(status='absent').count(),
        }
        training_sites_stats.append(site_stats)

    context = {
        'total_attendances': total_attendances,
        'present_count': present_count,
        'absent_count': absent_count,
        'training_sites_stats': training_sites_stats,
    }

    return render(request, 'doctor_section/attendance_summary.html', context)


@login_required
def debug_doctor_status(request):
    """Debug view to check doctor status and mappings"""
    debug_info = {
        'user_authenticated': request.user.is_authenticated,
        'user_role': getattr(request.user, 'role', 'No role attribute'),
        'username': request.user.username,
        'user_id': request.user.id,
    }

    # Check doctor profile
    try:
        doctor = request.user.doctor_profile
        debug_info['doctor_profile_exists'] = True
        debug_info['doctor_id'] = doctor.id
        debug_info['doctor_departments'] = [dept.name for dept in doctor.departments.all()]

        # Check mapped attendances
        mapped_attendances = MappedAttendance.objects.filter(doctors=doctor)
        active_mappings = mapped_attendances.filter(is_active=True)

        debug_info['total_mappings'] = mapped_attendances.count()
        debug_info['active_mappings'] = active_mappings.count()
        debug_info['mapping_details'] = [
            {
                'id': ma.id,
                'name': ma.name,
                'training_site': ma.training_site.name,
                'is_active': ma.is_active,
                'groups_count': ma.groups.count(),
                'groups': [group.group_name for group in ma.groups.all()]
            }
            for ma in mapped_attendances
        ]

        # Check all mapped attendances in system
        all_mappings = MappedAttendance.objects.all()
        debug_info['total_system_mappings'] = all_mappings.count()
        debug_info['all_doctors_in_mappings'] = list(set([
            doctor.user.username for mapping in all_mappings for doctor in mapping.doctors.all()
        ]))

    except Doctor.DoesNotExist:
        debug_info['doctor_profile_exists'] = False
        debug_info['doctor_error'] = 'Doctor profile does not exist'

        # Check if any doctor profiles exist
        all_doctors = Doctor.objects.all()
        debug_info['total_doctors_in_system'] = all_doctors.count()
        debug_info['all_doctor_usernames'] = [d.user.username for d in all_doctors]

    except AttributeError as e:
        debug_info['doctor_profile_exists'] = False
        debug_info['doctor_error'] = f'AttributeError: {str(e)}'

    return JsonResponse(debug_info, indent=2)
