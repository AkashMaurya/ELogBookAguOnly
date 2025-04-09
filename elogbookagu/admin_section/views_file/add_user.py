from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db import transaction
from accounts.models import CustomUser, Student, Doctor, Staff
from admin_section.forms import CustomUserForm


def add_user(request):
    # Handle form submission
    if request.method == 'POST':
        form = CustomUserForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()

                # Create role-specific profile based on the selected role
                if user.role == 'student':
                    Student.objects.create(user=user)
                    messages.success(request, f'Student user {user.username} created successfully!')
                elif user.role == 'doctor':
                    Doctor.objects.create(user=user)
                    messages.success(request, f'Doctor user {user.username} created successfully!')
                elif user.role == 'staff':
                    Staff.objects.create(user=user)
                    messages.success(request, f'Staff user {user.username} created successfully!')
                else:  # admin
                    messages.success(request, f'Admin user {user.username} created successfully!')

            return redirect('admin_section:add_user')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomUserForm()

    # Get all users for the table
    users = CustomUser.objects.all().order_by('-date_joined')

    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'users': page_obj,
    }

    return render(request, "admin_section/add_user.html", context)


def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        # For editing, we don't want to change the password
        form = CustomUserForm(request.POST, request.FILES, instance=user)

        # Remove password fields validation for edit
        form.fields['password1'].required = False
        form.fields['password2'].required = False

        if form.is_valid():
            user = form.save(commit=False)
            # Only update password if provided
            if form.cleaned_data.get('password1'):
                user.set_password(form.cleaned_data['password1'])
            user.save()

            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('admin_section:add_user')
    else:
        form = CustomUserForm(instance=user)
        # Remove password fields validation for edit
        form.fields['password1'].required = False
        form.fields['password2'].required = False

    context = {
        'form': form,
        'user_obj': user,
        'is_edit': True,
    }

    return render(request, "admin_section/add_user.html", context)


def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        try:
            username = user.username
            user.delete()
            messages.success(request, f'User {username} deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')
        return redirect('admin_section:add_user')

    # If it's an AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    # Otherwise, redirect to the user list
    return redirect('admin_section:add_user')
