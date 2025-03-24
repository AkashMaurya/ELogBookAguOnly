from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from admin_section.models import *
from accounts.models import Student,Doctor

# Django predefied models
from django.db.models import Count


# Create your views here.


@login_required
def admin_dash(request):
    # Counting 
    total_activities = ActivityType.objects.count()
    total_departments = Department.objects.count()

    total_student = Student.objects.count()
    total_doctors = Doctor.objects.count()
    


    print(total_student)
    data = {
        "total_activities": total_activities,
        "total_departments": total_departments,
        "total_student": total_student,
        "total_doctors": total_doctors,
    }

    return render(request, "admin_section/admin_dash.html", data)


@login_required
def admin_blogs(request):
    return render(request, "admin_section/admin_blogs.html")


@login_required
def admin_profile(request):
    return render(request, "admin_section/admin_profile.html")


@login_required
def admin_reviews(request):
    return render(request, "admin_section/admin_reviews.html")


@login_required
def admin_support(request):
    return render(request, "admin_section/admin_support.html")


@login_required
def final_records(request):
    return render(request, "admin_section/admin_final_record.html")
