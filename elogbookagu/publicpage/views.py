from django.shortcuts import render, get_object_or_404, redirect
from admin_section.models import Department, TrainingSite
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import time
import datetime
from django.core.exceptions import ValidationError
from accounts.models import CustomUser, Student, Staff, Doctor
import os  # Moved os import here
from django.http import FileResponse
from django.conf import settings
from django.db import models
from django.core.paginator import Paginator
from django.db.models import Sum
from student_section.models import StudentLogFormModel


def get_site_statistics():
    """
    Helper function to calculate and format site statistics
    Returns a dictionary with formatted statistics
    """
    # Count users by role
    doctor_count = CustomUser.objects.filter(role='doctor').count()
    staff_count = CustomUser.objects.filter(role='staff').count()
    student_count = CustomUser.objects.filter(role='student').count()
    admin_count = CustomUser.objects.filter(role='admin').count()

    # Total active users
    total_users = doctor_count + staff_count + student_count + admin_count

    # Count institutions (training sites)
    total_institutions = TrainingSite.objects.count()

    # For resources accessed, use log entries + a multiplier to represent page views
    log_entries = StudentLogFormModel.objects.count()
    # Assuming each log entry represents multiple page views/resources
    estimated_resources = log_entries * 10  # Multiplier to estimate total resources accessed

    # Format numbers with commas for thousands
    formatted_users = f"{total_users:,}+"
    formatted_institutions = f"{total_institutions:,}+"
    formatted_resources = f"{estimated_resources:,}+"

    # Use actual numbers, don't override with minimums

    return {
        'active_users': formatted_users,
        'institutions': formatted_institutions,
        'resources_accessed': formatted_resources,
        'support_available': '24/7',  # This is a static value
        'doctor_count': f"{doctor_count:,}",
        'staff_count': f"{staff_count:,}",
        'student_count': f"{student_count:,}",
        'admin_count': f"{admin_count:,}",
        'total_users': f"{total_users:,}"
    }

# Create your views here.


def home(request):
    # Get statistics from helper function
    context = get_site_statistics()
    return render(request, "home.html", context)


def about(request):
    # Get statistics from helper function
    context = get_site_statistics()
    return render(request, "about.html", context)


def resources(request):
    return render(request, "resources.html")


def update(request):
    # Get filter parameters
    category = request.GET.get('category', '')
    search_query = request.GET.get('q', '').strip()

    # Import the Blog model from admin_section
    from admin_section.models import Blog

    # Base queryset - only published blogs
    blogs = Blog.objects.filter(is_published=True)

    # Apply filters
    if category:
        blogs = blogs.filter(category=category)

    if search_query:
        blogs = blogs.filter(
            models.Q(title__icontains=search_query) |
            models.Q(summary__icontains=search_query) |
            models.Q(content__icontains=search_query)
        )

    # Order by most recent first
    blogs = blogs.order_by('-created_at')

    # Pagination
    paginator = Paginator(blogs, 9)  # 9 items per page for grid layout
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'blogs': page_obj,
        'selected_category': category,
        'search_query': search_query,
        'categories': Blog.CATEGORY_CHOICES,
    }

    return render(request, "update.html", context)


def blog_detail(request, blog_id):
    """View for displaying a single blog post to the public"""
    # Import the Blog model from admin_section
    from admin_section.models import Blog

    # Get the blog post - only published blogs are visible to the public
    blog = get_object_or_404(Blog, id=blog_id, is_published=True)

    # Get related blogs (same category, excluding current blog)
    related_blogs = Blog.objects.filter(
        category=blog.category,
        is_published=True
    ).exclude(id=blog.id).order_by('-created_at')[:3]

    context = {
        'blog': blog,
        'related_blogs': related_blogs,
        'categories': Blog.CATEGORY_CHOICES,
    }

    return render(request, "blog_detail.html", context)


def ebookjournals(request, pdf_name=None):
    if pdf_name:  # If a specific PDF is requested
        pdf_path = os.path.join(settings.MEDIA_ROOT, f"{pdf_name}.pdf")
        try:
            pdf_file = open(pdf_path, "rb")
            response = FileResponse(pdf_file, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{pdf_name}.pdf"'
            return response
        except FileNotFoundError:
            # Optionally handle the error differently
            pass

    # If no PDF requested or file not found, return the template
    return render(request, "ebookjournals.html")


def login(request):
    # Agar user pehle se login hai to redirect karen
    # if request.user.is_authenticated:
    #     return redirect("dashboard")

    # Agar request method POST hai, to form se data handle karen
    if request.method == "POST":
        email = (
            request.POST.get("email").strip().lower()
        )  # Email ko strip aur lower case mein convert karen
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
        messages.success(
            request, f"Welcome {user.email}!"
        )  # Login hone par success message dikhayein

        # Seesion mein user ki details save karen
        request.session["username"] = (
            user.username.upper()
        )  # Username ko uppercase mein store karen
        request.session["first_name"] = user.first_name  # First name store karen
        request.session["last_name"] = user.last_name  # Last name store karen
        request.session["profile_photo"] = (
            user.profile_photo.url
            if user.profile_photo and user.profile_photo.url
            else "/media/profiles/default.jpg"
        )  # Profile photo ko store karen, agar photo nahi hai to default image ka path set karen
        request.session["role"] = user.role  # Role ko session mein save karen
        request.session["city"] = user.city  # City ko session mein save karen
        request.session["country"] = user.country  # Country ko session mein save karen
        request.session["phone_no"] = (
            user.phone_no
        )  # Phone number ko session mein save karen
        request.session["bio"] = user.bio  # Bio ko session mein save karen
        request.session["speciality"] = (
            user.speciality
        )  # Speciality ko session mein save karen
        request.session["email"] = user.email  # Email ko session mein save karen

        # Add student group data if user is a student
        if user.role == "student":
            try:
                student = Student.objects.get(user=user)
                if student.group:
                    request.session["group_name"] = student.group.group_name
                    request.session["log_year"] = (
                        student.group.log_year.year_name
                        if student.group.log_year
                        else None
                    )
                    request.session["log_year_section"] = (
                        student.group.log_year_section.year_section_name
                        if student.group.log_year_section
                        else None
                    )
                    # Add debug prints
                    print("Group Name:", student.group.group_name)
                    print(
                        "Log Year:",
                        (
                            student.group.log_year.year_name
                            if student.group.log_year
                            else None
                        ),
                    )
                    print(
                        "Section:",
                        (
                            student.group.log_year_section.year_section_name
                            if student.group.log_year_section
                            else None
                        ),
                    )
            except Student.DoesNotExist:
                print(f"No student profile found for user: {user.email}")
                request.session["group_name"] = None
                request.session["log_year"] = None
                request.session["log_year_section"] = None

        # Staff data handling
        if user.role == "staff":
            try:
                staff = Staff.objects.select_related('user').get(user=user)
                departments = staff.get_departments()
                request.session["departments"] = departments
            except Staff.DoesNotExist:
                print(f"No staff profile found for user: {user.email}")
                request.session["departments"] = []
                messages.warning(request, "Staff profile not found. Please contact administrator.")
            except Exception as e:
                print(f"Error fetching staff departments: {str(e)}")
                request.session["departments"] = []

        request.session.save()  # Session ko explicitly save karen

        # User ke role ke hisaab se redirection
        role_redirects = {
            "admin": "admin_section:admin_dash",  # Admin role ke liye dashboard redirect
            "doctor": "doctor_section:doctor_dash",  # Doctor role ke liye dashboard redirect
            "student": "student_section:student_dash",  # Student role ke liye dashboard redirect
            "staff": "staff_section:staff_dash",  # Staff role ke liye dashboard redirect
        }

        # Agar role valid hai to uss role ke dashboard par redirect karen, warna default "dashboard" par
        return redirect(role_redirects.get(user.role, "dashboard"))

    # Agar GET request hai, to login page render karen
    current_year = datetime.datetime.now().year
    return render(request, "login.html", {"current_year": current_year})


def logout(request):
    logout(request)
    messages.success(request, "Successfully logged out!")
    return redirect("login")
