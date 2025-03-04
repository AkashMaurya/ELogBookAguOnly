from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import time  # Brute-force attack रोकने के लिए (optional)
from django.core.exceptions import ValidationError
from accounts.models import CustomUser , Student
from django.shortcuts import render, redirect


# Create your views here.


def home(request):
    return render(request, "home.html")


def about(request):
    return render(request, "about.html")


def resources(request):
    return render(request, "resources.html")


def update(request):
    return render(request, "update.html")



def login(request):
    # Agar user pehle se login hai to redirect karen
    # if request.user.is_authenticated:
    #     return redirect("dashboard")

    # Agar request method POST hai, to form se data handle karen
    if request.method == "POST":
        email = request.POST.get("email").strip().lower()  # Email ko strip aur lower case mein convert karen
        password = request.POST.get("password")  # Password le rahe hain

        # Agar email ya password nahi hai, to error message dikhayein
        if not email or not password:
            messages.error(request, "Email और Password दोनों आवश्यक हैं!")  # Error message
            return redirect("login")  # Login page par redirect karein

        # Authenticate karen: user ko email aur password se check karen
        user = authenticate(request, username=email, password=password)

        # Agar user valid nahi hai, to error message dikhayein aur brute-force attack se bachne ke liye thodi der wait karen
        if user is None:
            messages.error(request, "Invalid email or password.")
            time.sleep(2)  # Brute-force attack se bachne ke liye
            return redirect("login")

        # Agar user authenticate ho gaya hai, to user ko login karayein
        auth_login(request, user)
        messages.success(request, f"Welcome {user.email}!")  # Login hone par success message dikhayein

        # Seesion mein user ki details save karen
        request.session["username"] = user.username.upper()  # Username ko uppercase mein store karen
        request.session["first_name"] = user.first_name  # First name store karen
        request.session["last_name"] = user.last_name  # Last name store karen
        request.session["profile_photo"] = (
            user.profile_photo.url if user.profile_photo and user.profile_photo.url else "/media/profiles/default.jpg"
        )  # Profile photo ko store karen, agar photo nahi hai to default image ka path set karen
        request.session["role"] = user.role  # Role ko session mein save karen
        request.session["city"] = user.city  # City ko session mein save karen
        request.session["country"] = user.country  # Country ko session mein save karen
        request.session["phone_no"] = user.phone_no  # Phone number ko session mein save karen
        request.session["bio"] = user.bio  # Bio ko session mein save karen
        request.session["speciality"] = user.speciality  # Speciality ko session mein save karen
        request.session["email"] = user.email  # Email ko session mein save karen
        
        # Add student group data if user is a student
        if user.role == "student":
            try:
                student = Student.objects.get(user=user)
                if student.group:
                    request.session["group_name"] = student.group.group_name
                    request.session["log_year"] = student.group.log_year.year_name if student.group.log_year else None
                    request.session["log_year_section"] = student.group.log_year_section.year_section_name if student.group.log_year_section else None
                    # Add debug prints
                    print("Group Name:", student.group.group_name)
                    print("Log Year:", student.group.log_year.year_name if student.group.log_year else None)
                    print("Section:", student.group.log_year_section.year_section_name if student.group.log_year_section else None)
            except Student.DoesNotExist:
                print(f"No student profile found for user: {user.email}")
                request.session["group_name"] = None
                request.session["log_year"] = None
                request.session["log_year_section"] = None

        request.session.save() # Session ko explicitly save karen

        # User ke role ke hisaab se redirection
        role_redirects = {
            "admin": "admin_section:admin_dash",  # Admin role ke liye dashboard redirect
            "doctor": "doctor_section:doctor_dash",  # Doctor role ke liye dashboard redirect
            "student": "student_section:student_dash",  # Student role ke liye dashboard redirect
            "staff": "staff_section:staff_dashboard",  # Staff role ke liye dashboard redirect
        }

        # Agar role valid hai to uss role ke dashboard par redirect karen, warna default "dashboard" par
        return redirect(role_redirects.get(user.role, "dashboard"))

    # Agar GET request hai, to login page render karen
    return render(request, "login.html")



def logout(request):
    logout(request)
    messages.success(request, "Successfully logged out!")
    return redirect("login")
