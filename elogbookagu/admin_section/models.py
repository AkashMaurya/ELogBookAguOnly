from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

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
