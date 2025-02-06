# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render

# Staff Dashboard View
def staff_dash(request):
    return HttpResponse("<h1>Welcome to the Staff Dashboard</h1>")

# Staff Blogs View
def staff_blogs(request):
    return HttpResponse("<h1>Staff Blogs</h1><p>Here you can read and write blogs.</p>")

# Staff Support View
def staff_support(request):
    return HttpResponse("<h1>Staff Support</h1><p>If you need assistance, please contact support.</p>")

# Staff Reviews View
def staff_reviews(request):
    return HttpResponse("<h1>Staff Reviews</h1><p>Here you can view and provide feedback on reviews.</p>")

# Staff Profile View
def staff_profile(request):
    return HttpResponse("<h1>Your Profile</h1><p>Update your personal information here.</p>")

# Staff Final Records View
def staff_final_records(request):
    return HttpResponse("<h1>Final Records</h1><p>View final records and reports here.</p>")
