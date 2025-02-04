from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import time  # Brute-force attack रोकने के लिए (optional)
from django.core.exceptions import ValidationError
from accounts.models import CustomUser


# Create your views here.


def home(request):
    return render(request, "home.html")


def about(request):
    return render(request, "about.html")


def resources(request):
    return render(request, "resources.html")


def update(request):
    return render(request, "update.html")


def contact(request):
    return render(request, "contact.html")


def login(request):
    """
    लॉगिन व्यू जो ईमेल और पासवर्ड से यूजर को ऑथेंटिकेट करता है और रोल के आधार पर रीडायरेक्ट करता है।
    """

    # if request.user.is_authenticated:
    #     return redirect("dashboard")  # पहले से लॉग इन है तो डायरेक्ट भेज दें

    if request.method == "POST":
        email = request.POST.get("email").strip().lower()
        password = request.POST.get("password")

        if not email or not password:
            messages.error(request, "Email और Password दोनों आवश्यक हैं!")
            return redirect("login")

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, "User इस ईमेल से मौजूद नहीं है।")
            return redirect("login")

        user = authenticate(request, username=user.email, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, f"Welcome {user.email}!")

            # Role-Based Redirects
            role_redirects = {
                "admin": "admin_section:admin_dash",
                "doctor": "doctor_section:doctor_dash",
                "student": "student_dashboard",
                "staff": "staff_dashboard",
            }

            return redirect(role_redirects.get(user.role, "dashboard"))

        else:
            messages.error(request, "Invalid email or password.")
            time.sleep(2)  # Brute-force को रोकने के लिए
            return redirect("login")

    return render(request, "login.html")


def logout(request):
    logout(request)
    messages.success(request, "Successfully logged out!")
    return redirect("login")
