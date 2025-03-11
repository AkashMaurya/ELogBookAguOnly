from django import forms
from admin_section.models import ActivityType, CoreDiaProSession
from publicpage.models import Department
import logging

logger = logging.getLogger(__name__)


class ActivityTypeForm(forms.ModelForm):
    # Adding an advanced field not in the model
    is_advanced = forms.BooleanField(
        label="Advanced Activity",
        required=False,
        help_text="Check if this is an advanced activity type",
    )

    class Meta:
        model = ActivityType
        fields = ["name", "department"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:text-white",
                    "placeholder": "Enter activity type name",
                }
            ),
            "department": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:text-white"
                }
            ),
        }
        labels = {
            "name": "Activity Name",
            "department": "Department",
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        department = cleaned_data.get("department")

        # Check for uniqueness
        if ActivityType.objects.filter(name=name, department=department).exists():
            raise forms.ValidationError(
                "An activity type with this name already exists in this department."
            )
        return cleaned_data


class CoreDiaProSessionForm(forms.ModelForm):
    class Meta:
        model = CoreDiaProSession
        fields = ["name", "activity_type", "department"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:text-white",
                    "placeholder": "Enter session name",
                }
            ),
            "activity_type": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:text-white"
                }
            ),
            "department": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:text-white"
                }
            ),
        }
        labels = {
            "name": "Session Name",
            "activity_type": "Activity Type",
            "department": "Department",
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        department = cleaned_data.get("department")
        activity_type = cleaned_data.get("activity_type")
        logger.debug(f"Data provided for a new session:{name},{department},{activity_type}")
        
        # Check for uniqueness
        try:
            if self.instance.pk:
                existing_sessions = CoreDiaProSession.objects.exclude(
                    pk=self.instance.pk
                )
            else:
                existing_sessions = CoreDiaProSession.objects.all()

            if existing_sessions.filter(
                name=name, department=department, activity_type=activity_type
            ).exists():
                raise forms.ValidationError(
                    "A session with this name already exists for this department and activity type."
                )
        except Exception as e:
            logger.error(f"Error validating unique fields:{e}")
            raise forms.ValidationError(
                "An error was raised while validating uniqueness"
            )
        return cleaned_data
