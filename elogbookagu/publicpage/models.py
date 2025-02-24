from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

# Django Signals (automatic actions when model instances are created or updated)
from django.db.models.signals import post_save
from django.dispatch import receiver


# Custom User Model (Extending AbstractUser)


# LogYear Model (For defining different academic years)
class LogYear(models.Model):
    """
    लॉग ईयर मॉडल जिसमें अलग-अलग वर्षों को नाम दिया जाएगा (Year 5, Year 6, आदि)।
    """

    year_name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.year_name


# LogYearSection Model (Divisions within a LogYear)
class LogYearSection(models.Model):
    """
    लॉग ईयर सेक्शन मॉडल जो प्रत्येक लॉग ईयर में सेक्शन (Year 5, Year 6) को दर्शाता है।
    """

    year_section_name = models.CharField(max_length=20)
    year_name = models.ForeignKey(
        LogYear, on_delete=models.CASCADE, related_name="log_year_sections"
    )
    is_deleted = models.BooleanField(default=False)  # Soft delete functionality

    def clean(self):
        """
        Validate that only 'Year 5' or 'Year 6' is allowed as a section name.
        """
        valid_sections = ["Year 5", "Year 6"]
        if self.year_section_name not in valid_sections:
            raise ValidationError(
                f"{self.year_section_name} is not a valid section name. It should be 'Year 5' or 'Year 6'."
            )

    def __str__(self):
        return self.year_section_name


# Department Model
class Department(models.Model):
    """
    विभाग (Department) मॉडल जो लॉग ईयर और सेक्शन से जुड़ा होता है।
    """

    name = models.CharField(max_length=50)
    log_year = models.ForeignKey(
        LogYear, on_delete=models.CASCADE, related_name="department_log_year"
    )
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


# Function to create default departments for each LogYearSection
def create_departments_for_log_year_section(log_year, year_section, department_names):
    """
    यह फंक्शन एक लॉग ईयर सेक्शन के लिए डिफ़ॉल्ट डिपार्टमेंट्स (Departments) क्रिएट करता है।
    """
    for name in department_names:
        if not Department.objects.filter(
            name=name, log_year=log_year, log_year_section=year_section
        ).exists():
            Department.objects.create(
                name=name, log_year=log_year, log_year_section=year_section
            )


# Signal: Automatically create departments when a new LogYearSection is added
@receiver(post_save, sender=LogYearSection)
def handle_log_year_section_creation(sender, instance, created, **kwargs):
    """
    जब भी कोई नया LogYearSection बनेगा, यह सिग्नल डिफ़ॉल्ट डिपार्टमेंट्स बनाएगा।
    """
    if created:
        log_year = instance.year_name
        year_section_name = instance.year_section_name.lower()

        if year_section_name == "year 5":
            create_departments_for_log_year_section(
                log_year, instance, ["Internal Medicine", "OBGYN", "Pediatrics"]
            )
        elif year_section_name == "year 6":
            create_departments_for_log_year_section(
                log_year,
                instance,
                ["ENT", "Surgery", "Family Medicine", "Ophthalmology", "Psychiatry"],
            )


# Group Model
class Group(models.Model):
    """
    ग्रुप मॉडल जो लॉग ईयर और लॉग ईयर सेक्शन से जुड़ा होता है।
    """

    group_name = models.CharField(max_length=50)
    log_year = models.ForeignKey(
        LogYear, on_delete=models.CASCADE, related_name="groups_log_year"
    )
    log_year_section = models.ForeignKey(
        LogYearSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groups_log_year_section",
    )

    def __str__(self):
        return f"{self.group_name} ({self.log_year.year_name}) - {self.log_year_section.year_section_name if self.log_year_section else 'No Section'}"


# Signal: Create default groups when a new LogYearSection is added
@receiver(post_save, sender=LogYearSection)
def creating_group_for_log_year_section(sender, instance, created, **kwargs):
    """
    जब भी कोई नया LogYearSection बनेगा, यह सिग्नल डिफ़ॉल्ट ग्रुप्स बनाएगा।
    """
    if created:
        log_year = instance.year_name
        year_section_name_cleaned = instance.year_section_name.strip().lower()

        group_mapping = {
            "year 5": ["B1", "B2", "B3", "B4"],
            "year 6": ["A1", "A2", "A3", "A4"],
        }

        group_names = group_mapping.get(year_section_name_cleaned, [])

        for group_name in group_names:
            if not Group.objects.filter(
                group_name=group_name, log_year=log_year, log_year_section=instance
            ).exists():
                Group.objects.create(
                    group_name=group_name, log_year=log_year, log_year_section=instance
                )


# Training Site Model
class TrainingSite(models.Model):
    """
    ट्रेनिंग साइट मॉडल जो लॉग ईयर से जुड़ा होता है।
    """

    name = models.CharField(max_length=100, unique=True)
    log_year = models.ForeignKey(
        LogYear, related_name="training_sites", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name


# Signal: Create default training sites when a new LogYear is added
@receiver(post_save, sender=LogYear)
def create_training_sites(sender, instance, created, **kwargs):
    """
    जब भी नया लॉग ईयर बनाया जाता है, यह सिग्नल ट्रेनिंग साइट्स जोड़ता है।
    """
    if created:
        training_sites = [
            "SMC",
            "KHUH",
            "MKCC",
            "Health Center",
            "Psychiatry Hospital",
            "AGU",
            "Medical Skill & Simulation Center",
        ]
        for site in training_sites:
            if not TrainingSite.objects.filter(name=site, log_year=instance).exists():
                TrainingSite.objects.create(name=site, log_year=instance)
