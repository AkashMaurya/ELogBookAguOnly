# student_section/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = "student_section"  # This is crucial for namespacing URLs

urlpatterns = [
    path("", views.student_dash, name="student_dash"),
    path("student_blogs/", views.student_blogs, name="student_blogs"),
    path("student_support/", views.student_support, name="student_support"),
    path("student_elog/", views.student_elog, name="student_elog"),
    path("student_profile/", views.student_profile, name="student_profile"),
    path("student_final_records/", views.student_final_records, name="student_final_records"),
    # ye django ka logout class based view jo apne aap logout karwa dega if user want to log out
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    
    
    
    # edit 
    path("update-contact-info/", views.update_contact_info, name="update_contact_info"),
    path('update_biography/', views.update_biography, name='update_biography'),
]
