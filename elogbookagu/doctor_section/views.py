from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from accounts.models import Doctor


@login_required
def doctor_dash(request):
    return render(request, "doctor_dash.html")



@login_required
def doctor_profile(request):
    # Get the currently logged-in user from the request
    user = request.user  # ✅ Ensure user object is available

    # Get the profile photo URL correctly
    if user.profile_photo:  # ✅ Check if user has a profile photo
        profile_photo = user.profile_photo.url
    else:
        profile_photo = "/media/profiles/default.jpg"  # Default image if no profile photo

    # Fetch other session data (making sure these values exist in session)
    username = request.session.get("username", "Guest").upper()
    first_name = request.session.get("first_name", "GuestFirstName").upper()
    last_name = request.session.get("last_name", "GuestLastName").upper()
    full_name = f"{first_name} {last_name}"  # Combine first and last name
    user_role = request.session.get("role", "guest").upper()  # Get the user's role
    user_city = request.session.get("city", "")  # User's city, default is empty
    user_country = request.session.get("country", "")  # User's country, default is empty
    user_phone = request.session.get("phone_no", "")  # User's phone, default is empty
    user_bio = request.session.get("bio", "")  # User's bio, default is empty
    user_speciality = request.session.get("speciality", "")  # User's speciality, default is empty
    user_email = request.session.get("email", "abc@example.com")  # User's email

    # List of editable fields, can be used for form rendering
    editable_fields = [
        "password", "profile_photo", "city", "country", "phone", "bio", "speciality",
    ]

    # Prepare the context dictionary with all the necessary data to render the template
    data = {
        "username": username,
        "full_name": full_name,
        "profile_photo": profile_photo,  # ✅ Now using user.profile_photo.url
        "user_role": user_role,
        "first_name": first_name,
        "last_name": last_name,
        "user_city": user_city,
        "user_country": user_country,
        "user_phone": user_phone,
        "user_bio": user_bio,
        "user_speciality": user_speciality,
        "user_email": user_email,
        "editable_fields": editable_fields,  # List of fields that can be edited
    }

    # Debugging to check the profile photo URL
    print(f"Profile Photo URL: {profile_photo}")  # For debugging, can be removed later

    # Render the template with the context data
    return render(request, "doctor_profile.html", data)


@login_required
def doctor_blogs(request):
    return render(request, "doctor_blogs.html")


@login_required
def doctor_help(request):
    return render(request, "doctor_help.html")


@login_required
def doctor_reviews(request):
    return render(request, "doctor_reviews.html")


def logout(request):
    auth_logout(request)
    # Clear the session username
    request.session.pop("username", None)
    return redirect("login")
