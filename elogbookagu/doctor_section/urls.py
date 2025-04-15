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
    path("delete-support-ticket/<int:ticket_id>/", views.delete_support_ticket, name="delete_support_ticket"),
    path("review-log/<int:log_id>/", views.review_log, name="review_log"),
    path("batch-review/", views.batch_review, name="batch_review"),
    path("notifications/", views.notifications, name="notifications"),
]




