# admin_section/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = "admin_section"  # This is crucial for namespacing URLs

urlpatterns = [
    path("", views.admin_dash, name="admin_dash"),
    path("admin_blogs/", views.admin_blogs, name="admin_blogs"),
    path("admin_support/", views.admin_support, name="admin_support"),
    path("admin_reviews/", views.admin_reviews, name="admin_reviews"),
    path("admin_profile/", views.admin_profile, name="admin_profile"),
    path("admin_final_records/", views.final_records, name="admin_final_records"),
    # ye django ka logout class based view jo apne aap logout karwa dega if user want to log out
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
