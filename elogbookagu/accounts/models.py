from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from publicpage.models import *


# Create your models here.
class CustomUser(AbstractUser):
    """
    कस्टम यूजर मॉडल जिसमें प्रोफाइल फोटो और रोल-आधारित परमिशन जोड़े गए हैं।
    """

    # Email ko unique banayein aur username ko optional banaayein
    email = models.EmailField(unique=True)
    profile_photo = models.ImageField(upload_to="profiles/", blank=True, null=True)

    # Define user roles
    ROLE_CHOICES = (
        ("student", "Student"),
        ("doctor", "Doctor"),
        ("staff", "Staff"),
        ("admin", "Admin"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="student")

    # Override default related names to avoid conflicts
    groups = models.ManyToManyField(
        "auth.Group", related_name="customuser_set", blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission", related_name="customuser_set", blank=True
    )

    USERNAME_FIELD = "email"  # Email ko username field ke roop mein use karo
    REQUIRED_FIELDS = ["username"]  # Superuser ke liye username zaroori hai

    def __str__(self):
        return self.email


# Student Model
class Student(models.Model):
    """
    स्टूडेंट मॉडल जो कस्टम यूजर, ग्रुप और अन्य विवरणों से जुड़ा होता है।
    """

    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE
    )
    student_id = models.CharField(max_length=20, unique=True)
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )

    def __str__(self):
        return self.user.username


# Doctor Model
class Doctor(models.Model):
    """
    डॉक्टर मॉडल जिसमें यूजर, डिपार्टमेंट और स्थान शामिल हैं।
    """

    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="doctor_profile"
    )
    departments = models.ManyToManyField(Department, related_name="doctors", blank=True)

    def __str__(self):
        return self.user.username


# Staff Model
class Staff(models.Model):
    """
    स्टाफ मॉडल जो केवल यूजर डिटेल्स को स्टोर करता है।
    """

    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="staff_profile"
    )

    def __str__(self):
        return self.user.username
