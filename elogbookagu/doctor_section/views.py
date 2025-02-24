from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from accounts.models import Doctor
from django.http import JsonResponse


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
        profile_photo = (
            "/media/profiles/default.jpg"  # Default image if no profile photo
        )

    # get Doctor Profile
    doctor = getattr(
        user, "doctor_profile", None
    )  # `related_name="doctor_profile"` से doctor प्राप्त करें

    # Get doctor's departments
    if doctor:
        doctor_departments = ", ".join(
            dept.name for dept in doctor.departments.all()
        )  # ✅ स्ट्रिंग में बदलें
    else:
        doctor_departments = (
            None  # ❌ Empty string ना रखें, ताकि `{% if doctor_departments %}` सही से चले
        )

    # Fetch other session data (making sure these values exist in session)
    username = request.session.get("username", "Guest").upper()
    first_name = request.session.get("first_name", "GuestFirstName").upper()
    last_name = request.session.get("last_name", "GuestLastName").upper()
    full_name = f"{first_name} {last_name}"  # Combine first and last name
    user_role = request.session.get("role", "guest").upper()  # Get the user's role
    user_city = request.session.get("city", "")  # User's city, default is empty
    user_country = request.session.get(
        "country", ""
    )  # User's country, default is empty
    user_phone = request.session.get("phone_no", "")  # User's phone, default is empty
    user_bio = request.session.get("bio", "")  # User's bio, default is empty
    user_speciality = request.session.get(
        "speciality", ""
    )  # User's speciality, default is empty
    user_email = request.session.get("email", "abc@example.com")  # User's email

    # List of editable fields, can be used for form rendering
    editable_fields = [
        "password",
        "profile_photo",
        "city",
        "country",
        "phone",
        "bio",
        "speciality",
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
        "doctor_departments": doctor_departments,
    }

    # Debugging to check the profile photo URL
    print(f"Profile Photo URL: {profile_photo}")  # For debugging, can be removed later
    print(f"Doctor Departments: {doctor_departments}")
    # Render the template with the context data
    return render(request, "doctor_profile.html", data)


@login_required
def update_contact_info(request):
    if request.method == "POST":
        phone = request.POST.get("phone")
        city = request.POST.get("city")
        country = request.POST.get("country")

        try:
            # Update user profile info
            user = request.user
            user.phone_no = phone
            user.city = city
            user.country = country
            user.save()

            # Update session data
            request.session['phone_no'] = phone
            request.session['city'] = city
            request.session['country'] = country
            request.session.modified = True

            return JsonResponse({
                "success": True,
                "user_phone": phone,
                "user_city": city,
                "user_country": country,
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def update_profile_photo(request):
    if request.method == 'POST' and request.FILES.get('profile_photo'):
        user = request.user
        # Delete old profile photo if it exists
        if user.profile_photo and hasattr(user.profile_photo, 'path'):
            try:
                if os.path.exists(user.profile_photo.path):
                    os.remove(user.profile_photo.path)
            except Exception as e:
                print(f"Error deleting old profile photo: {e}")

        # Save new profile photo
        user.profile_photo = request.FILES['profile_photo']
        user.save()

        return JsonResponse({
            'success': True,
            'profile_photo': user.profile_photo.url
        })

    return JsonResponse({
        'success': False,
        'error': 'No photo provided'
    })



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
