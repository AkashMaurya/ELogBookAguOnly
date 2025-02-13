from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from publicpage.models import *

# Create your models here.
class CustomUser(AbstractUser):
    """
    कस्टम यूजर मॉडल जिसमें ईमेल लॉगिन, प्रोफाइल फोटो और रोल-आधारित परमिशन हैं।
    """

    email = models.EmailField(unique=True)  # ईमेल को यूनीक बनाया गया है
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    profile_photo = models.ImageField(
        upload_to="profiles/", blank=True, null=True, default="profiles/default.jpg"
    )  # यदि फोटो अपलोड न हो तो डिफ़ॉल्ट इमेज दिखे
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    phone_no = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    speciality  = models.CharField(max_length=100, blank=True)
    ROLE_CHOICES = (
        ("student", "Student"),
        ("doctor", "Doctor"),
        ("staff", "Staff"),
        ("admin", "Admin"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="student")

    groups = models.ManyToManyField(
        "auth.Group", related_name="customuser_groups", blank=True
    )  # related_name को बदला गया
    user_permissions = models.ManyToManyField(
        "auth.Permission", related_name="customuser_permissions", blank=True
    )  # related_name को बदला गया

    USERNAME_FIELD = "email"  # अब लॉगिन ईमेल से होगा
    REQUIRED_FIELDS = ["username"]  # सुपरयूजर के लिए यूज़रनेम जरूरी रहेगा


    def get_role_profile(self):
        """
        यह method ऑटोमैटिकली role के हिसाब से संबंधित डेटा देगा।
        """
        if self.role == "doctor":
            return getattr(self, "doctor_profile", None)
        elif self.role == "student":
            return getattr(self, "student", None)
        elif self.role == "staff":
            return getattr(self, "staff_profile", None)
        return None

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = "admin"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} ({self.role}), {self.username}"

# Student Model
class Student(models.Model):
    """
    स्टूडेंट मॉडल जिसमें यूजर, स्टूडेंट आईडी और ग्रुप की जानकारी होगी।
    """

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE , related_name="student")
    student_id = models.CharField(max_length=30, unique=True)  # अधिकतम लंबाई बढ़ाई गई
    group = models.ForeignKey("publicpage.Group", on_delete=models.SET_NULL, null=True, blank=True, related_name="students")


    def __str__(self):
        return self.user.username


# Doctor Model
class Doctor(models.Model):
    """
    डॉक्टर मॉडल जिसमें यूजर और डिपार्टमेंट की जानकारी होगी।
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="doctor_profile")
    departments = models.ManyToManyField("publicpage.Department", related_name="doctors", blank=True)
    
    def __str__(self):
        return self.user.username

    def get_departments(self):
        """
        डॉक्टर के सभी डिपार्टमेंट्स को एक स्ट्रिंग में बदल कर दिखाना।
        """
        departments = [department.name for department in self.departments.all()]
        return ", ".join(departments) if departments else "No Departments"


# Staff Model
class Staff(models.Model):
    """
    स्टाफ मॉडल जो केवल यूजर डिटेल्स को स्टोर करता है।
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="staff_profile")

    def __str__(self):
        return self.user.username
