from django.shortcuts import render, get_object_or_404

# Create your views here.


def home(request):
    return render(request, "home.html")


def about(request):
    return render(request, "about.html")



def resources(request):
    return render(request, "resources.html")

def update(request):
    return render(request, "update.html")

def contact(request):
    return render(request, "contact.html")

def login(request):
    return render(request, "login.html")