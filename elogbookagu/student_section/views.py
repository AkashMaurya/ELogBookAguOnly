from django.shortcuts import render
from accounts.models import Student, CustomUser
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

# Create your views here.

@login_required
def student_dash(request):
    return render(request, "student_dash.html")

@login_required
def student_blogs(request):
    return render(request, "student_blogs.html")

@login_required
def student_support(request):
    return render(request, "student_support.html")

@login_required
def student_elog(request):
    return render(request, "student_elog.html")

@login_required
def student_profile(request):
    # getting the User 
    user = request.user
    print("Current User:", user.email, "Role:", getattr(user, 'role', None))  # Debug print
    
    # getting the user photo
    if user.profile_photo:
        profile_photo = user.profile_photo.url
    else:
        profile_photo = "/media/profiles/default.jpg"

    # get Student Profile with related group data using select_related
    try:
        student = Student.objects.select_related('group', 'group__log_year', 'group__log_year_section').get(user=user)
        print("Found student:", student)  # Debug print
        print("Student Group:", getattr(student, 'group', None))  # Debug print
    except Student.DoesNotExist:
        student = None
        print("No student profile found for user:", user.email)
    
    # Initialize variables
    group_info = None
    log_year = None
    log_year_section = None
    group_full_info = None
    
    # Get group information if student exists and has a group
    if student and student.group:
        group = student.group
        print("Group details:", {  # Debug print
            'name': group.group_name,
            'log_year': getattr(group.log_year, 'year_name', None),
            'section': getattr(group.log_year_section, 'year_section_name', None)
        })
        
        group_info = group.group_name
        log_year = group.log_year.year_name if group.log_year else None
        log_year_section = group.log_year_section.year_section_name if group.log_year_section else None
        group_full_info = str(group)
    
    data = {
        'profile_photo': profile_photo,
        'full_name': f"{user.first_name} {user.last_name}",
        'user_email': user.email,
        'user_phone': user.phone_no,
        'user_city': user.city,
        'user_country': user.country,
        'user_bio': user.bio if hasattr(user, 'bio') else "",
        'group_name': group_info,
        'log_year': log_year,
        'log_year_section': log_year_section,
        'group_full_info': group_full_info
    }
    
    print("Final data being sent to template:", {  # Debug print
        'group_name': data['group_name'],
        'log_year': data['log_year'],
        'log_year_section': data['log_year_section'],
        'group_full_info': data['group_full_info']
    })
    
    return render(request, "student_profile.html", data)



# edit profile contact
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


# edit profile bio
@login_required
def update_biography(request): 
    if request.method == 'POST':
        biography = request.POST.get("biography")

        try:
            user = request.user
            user.bio = biography
            user.save()

            # Update session data
            request.session['bio'] = biography
            request.session.modified = True

            return JsonResponse({
                "success": True,
                "user_bio": biography
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})



@login_required
def student_final_records(request):
    return render(request, "student_final_recor ds.html")




