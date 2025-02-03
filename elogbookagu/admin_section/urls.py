from django.urls import path
from . import views

urlpatterns = [
    path("", views.admin_dash, name="admin_dash"),
    path("admin_blogs/", views.admin_blogs, name="admin_blogs"),
    path("admin_support/", views.admin_support, name="admin_support"),
    path("admin_reviews/", views.admin_reviews, name="admin_reviews"),
    path("admin_profile/", views.admin_profile, name="admin_profile"),
    path("admin_final_records/", views.final_records, name="admin_final_records"),
]
