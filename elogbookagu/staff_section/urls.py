# staff_section/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = "staff_section"  # This is crucial for namespacing URLs

urlpatterns = [
    path("", views.staff_dash, name="staff_dash"),

    path("staff_support/", views.staff_support, name="staff_support"),
    path("delete_support_ticket/<int:ticket_id>/", views.delete_support_ticket, name="delete_support_ticket"),
    path("staff_reviews/", views.staff_reviews, name="staff_reviews"),
    path("review_log/<int:log_id>/", views.review_log, name="review_log"),
    path("batch_review/", views.batch_review, name="batch_review"),
    path("staff_profile/", views.staff_profile, name="staff_profile"),
    path("notifications/", views.notifications, name="notifications"),
    # ye django ka logout class based view jo apne aap logout karwa dega if user want to log out
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
