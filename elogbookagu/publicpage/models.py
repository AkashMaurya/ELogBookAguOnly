from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Adding custom fields
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)

    # Role-based permissions
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('doctor', 'Doctor'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    # Override related_name to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group', 
        related_name='customuser_set', 
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission', 
        related_name='customuser_set', 
        blank=True
    )

    def __str__(self):
        return self.username

class LogYear(models.Model):
    year_name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.year_name
class LogYearSection(models.Model):
    year_section_name = models.CharField(max_length=20, unique=True)
    year_name = models.ForeignKey(LogYear, on_delete=models.CASCADE, related_name='LogYear')
    def __str__(self):
        return self.year_section_name

class Department(models.Model):
    name = models.CharField(max_length=50)
    log_year = models.ForeignKey(LogYear, on_delete=models.CASCADE, related_name='departments')

    def __str__(self):
        return f"{self.name} ({self.log_year.year_name})"

class Group(models.Model):
    name = models.CharField(max_length=50)
    log_year = models.ForeignKey(LogYear, on_delete=models.CASCADE, related_name='groups')

    def __str__(self):
        return f"{self.name} ({self.log_year.year_name})"

class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Doctor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='doctor_profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctors')
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Staff(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='staff_profile')
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username

# Custom Admin model for admin-only CRUD operations
class AdminProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='admin_profile')

    def __str__(self):
        return self.user.username
