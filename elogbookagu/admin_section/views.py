from django.shortcuts import render

# Create your views here.
def admin_dash(request):
    return render(request, 'admin_dashboard.html')


def admin_blogs(request):
    return render(request, 'admin_blogs.html')


def admin_profile(request):
    return render(request, 'admin_profile.html')

def admin_reviews(request):
    return render(request, 'admin_reviews.html')


def admin_support(request):
    return render(request, 'admin_support.html')

def final_records(request):
    return render(request, 'admin_final_record.html')