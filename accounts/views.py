from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render

from .forms import DeleteAccountForm, ProfileForm, UserForm
from .models import Profile


@login_required
def center_home(request):
    """Account Center overview."""
    return render(request, "account/center_home.html")


@login_required
def center_profile(request):
    """Edit base user fields + extended profile in one form submission."""
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(
            request.POST, request.FILES, instance=profile
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:center_profile")
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    return render(
        request,
        "account/center_profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "profile": profile,
        },
    )


@login_required
def center_password(request):
    """Change password while staying logged in."""
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keep the session alive
            messages.success(request, "Password changed.")
            return redirect("accounts:center_password")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "account/center_password.html", {"form": form})


@login_required
def center_delete(request):
    """Danger zone: delete the account."""
    if request.method == "POST":
        form = DeleteAccountForm(request.POST)
        if form.is_valid():
            user = request.user
            user.delete()
            messages.success(request, "Your account has been deleted.")
            return redirect("core:home")
    else:
        form = DeleteAccountForm()

    return render(request, "account/center_delete.html", {"form": form})