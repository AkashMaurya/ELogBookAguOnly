from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home_page"),
    path("about/", views.about, name="about_page"),
    path("resources/", views.resources, name="resources_page"),
    path("update/", views.update, name="update_page"),
    path("contact/", views.contact, name="contact_page"),
    path("login/", views.login, name="login"),
  
]
