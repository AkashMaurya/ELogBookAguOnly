from django.urls import path
from . import views

urlpatterns = [
    path("", views.doctor_dash, name="doctor_dash"),
    path("doctor_blogs/", views.doctor_blogs, name="doctor_blogs"),
    path("doctor_help/", views.doctor_help, name="doctor_help"),
    path("doctor_reviews/", views.doctor_reviews, name="doctor_reviews"),
    path("doctor_profile/", views.doctor_profile, name="doctor_profile"),
]
