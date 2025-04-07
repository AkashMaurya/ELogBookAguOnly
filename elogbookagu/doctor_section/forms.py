from django import forms
from .models import DoctorSupportTicket
from student_section.models import StudentLogFormModel

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
