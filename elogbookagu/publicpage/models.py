from django.contrib.auth.models import AbstractUser
from django.db import models

# for creating automatically Groups with signals and receiver
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUser(AbstractUser):
    # Adding custom fields
    profile_photo = models.ImageField(upload_to="profiles/", blank=True, null=True)

    # Role-based permissions
    ROLE_CHOICES = (
        ("student", "Student"),
        ("doctor", "Doctor"),
        ("staff", "Staff"),
        ("admin", "Admin"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="student")

    # Override related_name to avoid clashes
    groups = models.ManyToManyField(
        "auth.Group", related_name="customuser_set", blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission", related_name="customuser_set", blank=True
    )

    def __str__(self):
        return self.username


class LogYear(models.Model):
    year_name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.year_name


class LogYearSection(models.Model):
    year_section_name = models.CharField(
        max_length=20,
    )
    year_name = models.ForeignKey(
        LogYear, on_delete=models.CASCADE, related_name="LogYear"
    )
    is_deleted = models.BooleanField(default=False)  # Soft deletion flag

    def __str__(self):
        return self.year_section_name


class Department(models.Model):
    name = models.CharField(max_length=50)
    log_year = models.ForeignKey(
        LogYear, on_delete=models.CASCADE, related_name="departments"
    )
    log_year_section = models.ForeignKey(
        LogYearSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="departments",
    )

    def __str__(self):
        return f"{self.name} ({self.log_year.year_name}), {self.log_year_section.year_section_name}"


# autometically creating the departments according to the and logyearsection
@receiver(post_save, sender=LogYearSection)
def create_department_for_section(sender, instance, created, **kwargs):
    if created:
        # Access the LogYear instance from the related field log_year
        log_year = (
            instance.year_name
        )  # Correctly access the LogYear instance from LogYearSection
        year_section_name = (
            instance.year_section_name
        )  # Access the year_section_name from the instance
        # Check if the log year is "Year 5"
        if year_section_name.lower() == "year 5":
            department_names = ["Internal Medicine", "OBGYN", "Pediatrics"]
            for name in department_names:
                # Check if the department already exists
                existing_department = Department.objects.filter(
                    name=name, log_year=log_year, log_year_section=instance
                ).first()

                if (
                    not existing_department
                ):  # If the department doesn't exist, create it
                    Department.objects.create(
                        name=name,
                        log_year=log_year,
                        log_year_section=instance,
                    )
        # Check if the log year is "Year 6"
        elif year_section_name.lower() == "year 6":
            department_names = [
                "ENT",
                "Surgery",
                "Family Medicine",
                "Ophthalmology",
                "Psychiatry",
            ]
            for name in department_names:
                # Check if the department already exists
                existing_department = Department.objects.filter(
                    name=name, log_year=log_year, log_year_section=instance
                ).first()

                if (
                    not existing_department
                ):  # If the department doesn't exist, create it
                    Department.objects.create(
                        name=name,
                        log_year=log_year,
                        log_year_section=instance,
                    )

        print(
            f"Departments checked/created for {log_year.year_name} - {instance.year_section_name}"
        )
    else:
        print(f"LogYearSection '{instance.year_section_name}' already exists")


class Group(models.Model):
    group_name = models.CharField(max_length=50)
    log_year = models.ForeignKey(
        LogYear, on_delete=models.CASCADE, related_name="groups"
    )
    log_year_section = models.ForeignKey(
        LogYearSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groups",
    )

    def __str__(self):
        # Check if log_year_section is not None before accessing its attribute
        if self.log_year_section:
            return f"{self.group_name} ({self.log_year.year_name}) and {self.log_year_section.year_section_name}"
        else:
            return f"{self.group_name} ({self.log_year.year_name}) and No Section"


# Signal receiver for creating groups when LogYearSection is created
@receiver(post_save, sender=LogYearSection)
def creating_group_for_log_year_section(sender, instance, created, **kwargs):
    if created:
        log_year = instance.year_name  # Access the LogYear instance
        year_section_name = (
            instance.year_section_name
        )  # Access the year_section_name from the instance

        # Determine the groups based on year_section_name
        if year_section_name.lower() == "year 5":
            group_names = ["B1", "B2", "B3", "B4"]
        elif year_section_name.lower() == "year 6":
            group_names = ["A1", "A2", "A3", "A4"]
        else:
            group_names = []

        # Check if the groups already exist for this year and section
        for group_name_obj in group_names:
            existing_group = Group.objects.filter(
                group_name=group_name_obj,  # Use 'group_name' instead of 'group_names'
                log_year=log_year,
                log_year_section=instance,
            ).first()

            if not existing_group:  # If the group doesn't exist, create it
                Group.objects.create(
                    group_name=group_name_obj,  # Use 'group_name' instead of 'group_names'
                    log_year=log_year,
                    log_year_section=instance,
                )
        print(f"Groups created for {year_section_name}")
    else:
        print(f"LogYearSection '{instance.year_section_name}' already exists")


class Student(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="student_profile"
    )
    student_id = models.CharField(max_length=20, unique=True)
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )

    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username


class Doctor(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="doctor_profile"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctors",
    )
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username


class Staff(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="staff_profile"
    )
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username


# Custom Admin model for admin-only CRUD operations
class AdminProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="admin_profile"
    )

    def __str__(self):
        return self.user.username


class TrainingSite(models.Model):
    name = models.CharField(max_length=100, unique=True)
    log_year = models.ForeignKey(
        LogYear, related_name="training_sites", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name


# Add Automatically Training Sites when LogYear is created
@receiver(post_save, sender=LogYear)
def create_training_sites(sender, instance, created, **kwargs):
    if created:
        log_year = instance.year_name  # Access the LogYear instance
        # Define the activity types you want to create
        training_sites = [
            "SMC",
            "KHUH",
            "MKCC",
            "Health Center",
            "Psychiatry Hospital",
            "AGU",
            "Medical Skill & Simulation Center",
        ]  # training Sites types

        for training_name in training_sites:
            # Check if the training site already exists for this log year
            if not TrainingSite.objects.filter(
                name=training_name, log_year=instance
            ).exists():
                TrainingSite.objects.create(name=training_name, log_year=instance)
            else:
                print(
                    f"Training site '{training_name}' already exists for log year '{instance}'"
                )

        print(f"Training sites created for log year '{instance}'")
    else:
        print(f"LogYear '{instance}' already exists")

