from django.shortcuts import render, redirect

def add_student(request):
    return render(request, "admin_section/add_student.html")
