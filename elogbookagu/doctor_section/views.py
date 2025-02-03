from django.shortcuts import render


def doctor_dash(request):
    return render(request, "doctor_dash.html")


def doctor_profile(request):
    return render(request, "doctor_profile.html")


def doctor_blogs(request):
    return render(request, "doctor_blogs.html")


def doctor_help(request):
    return render(request, "doctor_help.html")


def doctor_reviews(request):
    return render(request, "doctor_reviews.html")


