from django.urls import path
from . import views  # For admin_dash, admin_blogs, etc.
from django.contrib.auth import views as auth_views
from .views_file.add_activity_views import (
    add_activity_type,
    edit_activity_type,
    delete_activity_type,
)
from .views_file.CoreDiaProSession_views import (
    core_dia_pro_session_list,
    core_dia_pro_session_create,
    core_dia_pro_session_update,
    core_dia_pro_session_delete,
    get_activity_types_by_department,
)

app_name = "admin_section"

urlpatterns = [
    # Other URLs
    path("", views.admin_dash, name="admin_dash"),
    path("admin_blogs/", views.admin_blogs, name="admin_blogs"),
    path("admin_support/", views.admin_support, name="admin_support"),
    path("admin_reviews/", views.admin_reviews, name="admin_reviews"),
    path("admin_profile/", views.admin_profile, name="admin_profile"),
    path("admin_final_records/", views.final_records, name="admin_final_records"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Activity Type URLs
    path("add_activity_type/", add_activity_type, name="add_activity_type"),
    path(
        "edit_activity_type/<int:activity_type_id>/",
        edit_activity_type,
        name="edit_activity_type",
    ),
    path(
        "delete_activity_type/<int:activity_type_id>/",
        delete_activity_type,
        name="delete_activity_type",
    ),
    path(
        'api/activity-types/<int:department_id>/',
        get_activity_types_by_department,
        name='get_activity_types_by_department'
    ),

    # Core Diagnosis Procedure Sessions URLs
    path('sessions/', core_dia_pro_session_list, name='core_dia_pro_session_list'),
    path('sessions/create/', core_dia_pro_session_create, name='core_dia_pro_session_create'),
    path('sessions/edit/<int:pk>/', core_dia_pro_session_update, name='core_dia_pro_session_update'),
    path('sessions/delete/<int:pk>/', core_dia_pro_session_delete, name='core_dia_pro_session_delete'),

    # Support Ticket URLs
    path('resolve_ticket/<int:ticket_id>/', views.resolve_ticket, name='resolve_ticket'),
]