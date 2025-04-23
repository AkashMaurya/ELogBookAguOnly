from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from accounts.models import CustomUser

# LogYear Model
class LogYear(models.Model):
    year_name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.year_name

# LogYearSection Model
class LogYearSection(models.Model):
    year_section_name = models.CharField(max_length=20)
    year_name = models.ForeignKey(LogYear, on_delete=models.CASCADE, related_name="log_year_sections")
    is_deleted = models.BooleanField(default=False)

    def clean(self):
        valid_sections = ["Year 5", "Year 6"]
        if self.year_section_name not in valid_sections:
            raise ValidationError(f"{self.year_section_name} is not a valid section name. It should be 'Year 5' or 'Year 6'.")

    def __str__(self):
        return self.year_section_name

# Department Model
class Department(models.Model):
    name = models.CharField(max_length=50)
    log_year = models.ForeignKey(LogYear, on_delete=models.CASCADE, related_name="department_log_year")
    log_year_section = models.ForeignKey(
        LogYearSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="department_log_year_section",
        db_index=True,
    )

    def __str__(self):
        return f"{self.name}"

# Group Model
class Group(models.Model):
    group_name = models.CharField(max_length=50)
    log_year = models.ForeignKey(LogYear, on_delete=models.CASCADE, related_name="groups_log_year")
    log_year_section = models.ForeignKey(
        LogYearSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groups_log_year_section",
    )

    def __str__(self):
        return f"{self.group_name} ({self.log_year.year_name}) - {self.log_year_section.year_section_name if self.log_year_section else 'No Section'}"

# TrainingSite Model
class TrainingSite(models.Model):
    name = models.CharField(max_length=100, unique=True)
    log_year = models.ForeignKey(LogYear, on_delete=models.CASCADE, related_name='training_sites')

    def __str__(self):
        return f"{self.name} ({self.log_year})"

# ActivityType Model
class ActivityType(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="activity_types")

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ["name", "department"]

# CoreDiaProSession Model
class CoreDiaProSession(models.Model):
    name = models.CharField(max_length=200)
    activity_type = models.ForeignKey(ActivityType, on_delete=models.CASCADE, related_name="core_dia_pro_sessions")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="core_dia_pro_sessions")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Core Diagnosis Procedure Session"
        verbose_name_plural = "Core Diagnosis Procedure Sessions"


# Date Restriction Settings Model
class DateRestrictionSettings(models.Model):
    # Original fields (for backward compatibility)
    past_days_limit = models.PositiveIntegerField(
        default=7,
        help_text="Maximum number of days in the past a student can select"
    )
    allow_future_dates = models.BooleanField(
        default=False,
        help_text="Whether students can select future dates"
    )
    future_days_limit = models.PositiveIntegerField(
        default=0,
        help_text="Maximum number of days in the future a student can select (if future dates are allowed)"
    )

    # Last updated timestamp
    updated_at = models.DateTimeField(auto_now=True)

    # Updated by
    updated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='date_restriction_updates'
    )

    # New fields for extended functionality
    # These will be added via migration

    # Specific days of week settings (for reference)
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    class Meta:
        verbose_name = "Date Restriction Setting"
        verbose_name_plural = "Date Restriction Settings"

    def __str__(self):
        return f"Date Restrictions (Past: {self.past_days_limit} days, Future: {'Allowed' if self.allow_future_dates else 'Not Allowed'})"

    # Properties for student settings
    @property
    def student_past_days_limit(self):
        return self.past_days_limit

    @property
    def student_allow_future_dates(self):
        return self.allow_future_dates

    @property
    def student_future_days_limit(self):
        return self.future_days_limit

    # Properties for doctor settings
    @property
    def doctor_past_days_limit(self):
        return getattr(self, '_doctor_past_days_limit', 30)

    @property
    def doctor_allow_future_dates(self):
        return getattr(self, '_doctor_allow_future_dates', False)

    @property
    def doctor_future_days_limit(self):
        return getattr(self, '_doctor_future_days_limit', 0)

    # Properties for allowed days
    @property
    def allowed_days_for_students(self):
        return getattr(self, '_allowed_days_for_students', "0,1,2,3,4,5,6")

    @property
    def allowed_days_for_doctors(self):
        return getattr(self, '_allowed_days_for_doctors', "0,1,2,3,4,5,6")

    @property
    def is_active(self):
        return getattr(self, '_is_active', True)

    # Helper methods for getting allowed days as lists
    def get_allowed_days_for_students(self):
        allowed_days_str = getattr(self, '_allowed_days_for_students', '0,1,2,3,4,5,6')
        return [int(day) for day in allowed_days_str.split(',') if day.strip()]

    def get_allowed_days_for_doctors(self):
        allowed_days_str = getattr(self, '_allowed_days_for_doctors', '0,1,2,3,4,5,6')
        return [int(day) for day in allowed_days_str.split(',') if day.strip()]

# Admin Notification Model
class AdminNotification(models.Model):
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='admin_notifications', limit_choices_to={'role': 'admin'})
    title = models.CharField(max_length=100)
    message = models.TextField()
    support_ticket_type = models.CharField(max_length=20, choices=[
        ('student', 'Student Support'),
        ('doctor', 'Doctor Support'),
        ('staff', 'Staff Support')
    ])
    ticket_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Admin Notification"
        verbose_name_plural = "Admin Notifications"

    def __str__(self):
        return f"{self.recipient.get_full_name()} - {self.title}"

    def mark_as_read(self):
        self.is_read = True
        self.save()
