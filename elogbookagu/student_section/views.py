from django.shortcuts import render

# Create your views here.


def student_dash(request):
    return render(request, "student_dash.html")


def student_blogs(request):
    return render(request, "student_blogs.html")


def student_support(request):
    return render(request, "student_support.html")


def student_elog(request):
    return render(request, "student_elog.html")


def student_profile(request):
    return render(request, "student_profile.html")


def student_final_records(request):
    return render(request, "student_final_records.html")
