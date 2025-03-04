from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = "doctor_section"  # This is crucial for namespacing URLs

urlpatterns = [
    path("", views.doctor_dash, name="doctor_dash"),
    path("doctor_blogs/", views.doctor_blogs, name="doctor_blogs"),
    path("doctor_help/", views.doctor_help, name="doctor_help"),
    path("doctor_reviews/", views.doctor_reviews, name="doctor_reviews"),
    path("doctor_profile/", views.doctor_profile, name="doctor_profile"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # edit profile
    path("update-contact-info/", views.update_contact_info, name="update_contact_info"),
    path('update-profile-photo/', views.update_profile_photo, name='update_profile_photo'),
    
  
]




