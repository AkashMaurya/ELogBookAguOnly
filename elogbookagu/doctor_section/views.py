from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def doctor_dash(request):
    return render(request, "doctor_dash.html")

@login_required
def doctor_profile(request):
    return render(request, "doctor_profile.html")

@login_required
def doctor_blogs(request):
    return render(request, "doctor_blogs.html")

@login_required
def doctor_help(request):
    return render(request, "doctor_help.html")

@login_required
def doctor_reviews(request):
    return render(request, "doctor_reviews.html")


