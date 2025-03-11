# admin_section/views_file/CoreDiaProSession_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .adding_forms import CoreDiaProSessionForm
from admin_section.models import CoreDiaProSession
import logging

logger = logging.getLogger(__name__)


@login_required
def core_dia_pro_session_list(request):
    print("Entering core_dia_pro_session_list view")
    sessions = CoreDiaProSession.objects.all().order_by("name")
    print(f"Found {sessions.count()} sessions")
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    if request.method == "POST" and "delete_id" in request.POST:
        session = get_object_or_404(CoreDiaProSession, pk=request.POST["delete_id"])
        session_name = session.name
        session.delete()
        messages.success(request, f'Session "{session_name}" deleted successfully!')
        return redirect("admin_section:core_dia_pro_session_list")

    context = {
        "core_sessions": page_obj,
        "form": CoreDiaProSessionForm(),
        "editing": False,
    }
    print("Rendering template")
    return render(request, "admin_section/core_dia_pro_session_list.html", context)

@login_required
def core_dia_pro_session_create(request):
    form = None
    try:
        if request.method == "POST":
            form = CoreDiaProSessionForm(request.POST)
            if form.is_valid():
                session = form.save(commit=False)
                session.save()
                messages.success(request, f'Session "{session.name}" created successfully!')
                return redirect("admin_section:core_dia_pro_session_list")
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = CoreDiaProSessionForm()
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        messages.error(request, "An error occurred while creating the session.")

    sessions = CoreDiaProSession.objects.all().order_by("name")
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    current_page = page_obj.number
    visible_page_range = range(max(1, current_page - 2), min(paginator.num_pages + 1, current_page + 3))

    context = {
        "core_sessions": page_obj,
        "form": form or CoreDiaProSessionForm(),
        "editing": False,
        "visible_page_range": visible_page_range,
    }
    return render(request, "admin_section/core_dia_pro_session_list.html", context)

@login_required
def core_dia_pro_session_update(request, pk):
    session = get_object_or_404(CoreDiaProSession, pk=pk)

    if request.method == "POST":
        form = CoreDiaProSessionForm(request.POST, instance=session)
        if form.is_valid():
            session = form.save(commit=False)

            session.save()
            messages.success(request, f'Session "{session.name}" updated successfully!')
            return redirect("admin_section:core_dia_pro_session_list")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CoreDiaProSessionForm(instance=session)

    sessions = CoreDiaProSession.objects.all().order_by("name")
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "core_sessions": page_obj,
        "form": form,
        "editing": True,
    }
    return render(request, "admin_section/core_dia_pro_session_list.html", context)


@login_required
def core_dia_pro_session_delete(request, pk):
    try:
        session = get_object_or_404(CoreDiaProSession, pk=pk)
        session.delete()
        messages.success(request, f'Session "{session.name}" deleted successfully!')
    except CoreDiaProSession.DoesNotExist:
        messages.error(request, "Session not found.")
    except Exception as e:
        print(f"Error: {e}")
        messages.error(request, "An error occurred while deleting the session.")
    return redirect("admin_section:core_dia_pro_session_list")
