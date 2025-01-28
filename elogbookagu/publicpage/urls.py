from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home-page"),
    path("about/", views.about, name="about-page"),
    path("resources/", views.resources, name="resources-page"),
    path("update/", views.update, name="update-page"),
    path("contact/", views.contact, name="contact-page"),
    path("login/", views.login, name="login-page"),
]
