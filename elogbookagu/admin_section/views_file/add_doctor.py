from django.shortcuts import render, redirect


def add_doctor(request):
    return render(request, "admin_section/add_doctor.html")
