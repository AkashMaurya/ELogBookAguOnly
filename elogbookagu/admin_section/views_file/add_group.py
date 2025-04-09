from django.shortcuts import render, redirect

def add_group(request):
    return render(request, "admin_section/add_group.html")
