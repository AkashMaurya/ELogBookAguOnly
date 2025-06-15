from django import forms
from django.utils import timezone
from datetime import date, timedelta
from .models import DoctorSupportTicket, StudentAttendance
from student_section.models import StudentLogFormModel
from accounts.models import Student
from admin_section.models import MappedAttendance, TrainingSite

class DoctorSupportTicketForm(forms.ModelForm):
    class Meta:
        model = DoctorSupportTicket
        fields = ['subject', 'description']
        widgets = {
            'subject': forms.TextInput(
                attrs={
                    'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                    'placeholder': 'Enter subject of your issue',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white h-32',
                    'placeholder': 'Describe your issue in detail',
                }
            ),
        }


class AdminDoctorResponseForm(forms.ModelForm):
    class Meta:
        model = DoctorSupportTicket
        fields = ['status', 'admin_comments']
        widgets = {
            'status': forms.Select(
                attrs={
                    'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                }
            ),
            'admin_comments': forms.Textarea(
                attrs={
                    'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white h-32',
                    'placeholder': 'Enter your response to the doctor',
                }
            ),
        }


class LogReviewForm(forms.ModelForm):
    REVIEW_CHOICES = [
        (True, 'Approve'),
        (False, 'Reject')
    ]

    is_approved = forms.ChoiceField(
        choices=REVIEW_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'mr-2'}),
        initial=True,
        required=True
    )

    class Meta:
        model = StudentLogFormModel
        fields = ['reviewer_comments']
        widgets = {
            'reviewer_comments': forms.Textarea(
                attrs={
                    'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white h-32',
                    'placeholder': 'Enter your comments (optional)',
                }
            ),
        }


class BatchReviewForm(forms.Form):
    log_ids = forms.CharField(widget=forms.HiddenInput())
    action = forms.ChoiceField(
        choices=[
            ('approve', 'Approve Selected'),
            ('reject', 'Reject Selected')
        ],
        widget=forms.RadioSelect(attrs={'class': 'mr-2'}),
        initial='approve'
    )
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white h-32',
                'placeholder': 'Enter comments for all selected logs (optional)',
            }
        )
    )


class AttendanceForm(forms.Form):
    """Form for taking attendance of multiple students"""
    training_site = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        empty_label="Select Training Site",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
        })
    )

    attendance_date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
            'max': date.today().isoformat(),  # Disable future dates
            'min': (date.today() - timedelta(days=30)).isoformat(),  # Allow up to 30 days back
            'value': date.today().isoformat(),  # Default to today but allow selection
        })
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white h-24',
            'placeholder': 'Optional notes about attendance (can be updated multiple times)',
            'rows': 3
        })
    )

    def __init__(self, doctor=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if doctor:
            # Get training sites where this doctor is mapped
            mapped_attendances = MappedAttendance.objects.filter(
                doctors=doctor,
                is_active=True
            ).select_related('training_site')

            training_site_ids = [ma.training_site.id for ma in mapped_attendances]
            self.fields['training_site'].queryset = TrainingSite.objects.filter(id__in=training_site_ids)

            # If only one training site, select it by default
            if len(training_site_ids) == 1:
                self.fields['training_site'].initial = training_site_ids[0]

    def clean_attendance_date(self):
        attendance_date = self.cleaned_data.get('attendance_date')
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        # Allow attendance for any day from today up to the last 30 days
        if attendance_date > today:
            raise forms.ValidationError("You cannot take attendance for future dates.")

        if attendance_date < thirty_days_ago:
            raise forms.ValidationError("You can only take attendance for dates within the last 30 days.")

        return attendance_date


class StudentAttendanceForm(forms.ModelForm):
    """Form for individual student attendance"""
    class Meta:
        model = StudentAttendance
        fields = ['status', 'notes']
        widgets = {
            'status': forms.RadioSelect(attrs={
                'class': 'mr-2'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'rows': 2,
                'placeholder': 'Optional notes'
            })
        }
