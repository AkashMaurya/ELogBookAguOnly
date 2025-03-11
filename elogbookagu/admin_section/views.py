from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

# Create your views here.


@login_required
def admin_dash(request):
    return render(request, "admin_section/admin_dash.html")


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

