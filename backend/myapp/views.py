from django.shortcuts import render, redirect
from django.http import HttpResponse
from supabase import create_client
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.hashers import make_password, check_password

# Initialize Supabase client
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)



def root_redirect(request):
    return redirect("/login/")


# --------------------------
# Registration View
# --------------------------
def register_page(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        username = request.POST.get("username", "").strip()
        role = "student"
        profile_picture = None
        bio = None
        last_login = None

        if not email or not password:
            return render(request, "register.html", {"error": "Email and password are required."})

        password_hash = make_password(password)

        existing = supabase.table("users").select("*").eq("email", email).execute()
        if existing.data:
            return render(request, "register.html", {"error": "Account already exists. Please login."})

        try:
            response = supabase.table("users").insert({
                "email": email,
                "password_hash": password_hash,
                "role": role,
                "username": username,
                "profile_picture": profile_picture,
                "bio": bio,
                "last_login": last_login,
                "date_joined": "now()"
            }).execute()

            if response.status_code != 201:
                return render(request, "register.html", {"error": f"Error registering: {response.error_message}"})

        except Exception as e:
            return render(request, "register.html", {"error": f"Error registering: {str(e)}"})

        return redirect("/login")

    return render(request, "register.html")


# --------------------------
# Login View
# --------------------------
def login_page(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        if not email or not password:
            return render(request, "login.html", {"error": "Email and password are required."})

        try:
            response = supabase.table("users").select("*").eq("email", email).execute()
        except Exception as e:
            return render(request, "login.html", {"error": f"Error connecting to database: {str(e)}"})

        if not response.data:
            return render(request, "login.html", {"error": "No account found. Please register."})

        user = response.data[0]

        if not check_password(password, user["password_hash"]):
            return render(request, "login.html", {"error": "Invalid credentials!"})

        # Save user session
        request.session["user_email"] = email
        request.session["role"] = user.get("role", "student")

        return redirect("/home/")

    return render(request, "login.html")

# --------------------------
# Password Recovery View
# --------------------------
def recover_password_page(request):
    import secrets
    from datetime import datetime, timedelta, timezone
    email = ""
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if not email:
            return render(request, "recover_password.html", {"error": "Email is required.", "email": email})
        # Check if user exists
        try:
            response = supabase.table("users").select("*").eq("email", email).execute()
        except Exception as e:
            return render(request, "recover_password.html", {"error": f"Error connecting to database: {str(e)}", "email": email})
        if not response.data:
            return render(request, "recover_password.html", {"error": "No account found with that email.", "email": email})
        user = response.data[0]
        user_id = user.get("id")
        if not user_id:
            return render(request, "recover_password.html", {"error": "User ID not found.", "email": email})
        # Generate secure token and expiration
        reset_token = secrets.token_urlsafe(32)
        expiration_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        created_at = datetime.now(timezone.utc).isoformat()
        # Store in password_recovery
        try:
            supabase.table("password_recovery").insert({
                "reset_token": reset_token,
                "expiration_time": expiration_time,
                "user_id": user_id,
                "created_at": created_at
            }).execute()
        except Exception as e:
            return render(request, "recover_password.html", {"error": f"Error saving reset token: {str(e)}", "email": email})
        # For testing, show the reset link directly
        reset_link = f"/reset-password/{reset_token}/"
        return render(request, "recover_password.html", {"error": None, "message": "If this email exists, a recovery link has been generated.", "email": email, "reset_link": reset_link})
    return render(request, "recover_password.html", {"email": email})

# --------------------------
# Password Reset View
# --------------------------
from django.contrib.auth.hashers import make_password

def reset_password_page(request, reset_token):
    from datetime import datetime, timezone
    # Look up the token in password_recovery
    try:
        token_resp = supabase.table("password_recovery").select("*", count="exact").eq("reset_token", reset_token).execute()
    except Exception as e:
        return render(request, "reset_password.html", {"error": f"Error looking up token: {str(e)}"})
    if not token_resp.data:
        return render(request, "reset_password.html", {"error": "Invalid or expired reset token."})
    token_row = token_resp.data[0]
    # Check expiration
    expiration_time = token_row.get("expiration_time")
    if not expiration_time:
        return render(request, "reset_password.html", {"error": "Token missing expiration."})
    try:
        expires = datetime.fromisoformat(expiration_time.replace('Z', '+00:00'))
    except Exception:
        expires = None
    if not expires or expires < datetime.now(timezone.utc):
        return render(request, "reset_password.html", {"error": "Reset token has expired."})
    # If POST, handle password reset (step 3 will complete this)
    if request.method == "POST":
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()
        if not new_password or not confirm_password:
            return render(request, "reset_password.html", {"error": "All fields are required.", "reset_token": reset_token})
        if new_password.strip() == "" or confirm_password.strip() == "":
            return render(request, "reset_password.html", {"error": "Password cannot be blank.", "reset_token": reset_token})
        if new_password != confirm_password:
            return render(request, "reset_password.html", {"error": "Passwords do not match.", "reset_token": reset_token})
        user_id = token_row.get("user_id") or token_row.get("id")
        if not user_id:
            return render(request, "reset_password.html", {"error": "User not found for this token.", "reset_token": reset_token})
        # Fetch current user password hash
        try:
            user_resp = supabase.table("users").select("password_hash").eq("id", user_id).execute()
            if not user_resp.data:
                return render(request, "reset_password.html", {"error": "User not found.", "reset_token": reset_token})
            current_hash = user_resp.data[0]["password_hash"]
        except Exception as e:
            return render(request, "reset_password.html", {"error": f"Error fetching user: {str(e)}", "reset_token": reset_token})
        # Prevent using the same password
        if check_password(new_password, current_hash):
            return render(request, "reset_password.html", {"error": "You cannot use your old password.", "reset_token": reset_token})
        password_hash = make_password(new_password)
        # Update user's password
        try:
            update_resp = supabase.table("users").update({"password_hash": password_hash}).eq("id", user_id).execute()
            if getattr(update_resp, 'error', None):
                return render(request, "reset_password.html", {"error": f"Failed to reset password: {update_resp.error}", "reset_token": reset_token})
        except Exception as e:
            return render(request, "reset_password.html", {"error": f"Error updating password: {str(e)}", "reset_token": reset_token})
        # Delete the used token
        try:
            supabase.table("password_recovery").delete().eq("reset_token", reset_token).execute()
        except Exception as e:
            return render(request, "reset_password.html", {"error": f"Password changed, but failed to clean up token: {str(e)}", "reset_token": reset_token})
        return render(request, "reset_password.html", {"message": "Password reset successful! You can now log in."})
    return render(request, "reset_password.html", {"reset_token": reset_token})



# --------------------------
# Home View (Protected)
# --------------------------
# This view requires the user to be logged in.
# If the user is not logged in, they will be redirected to the login page.
def home_page(request):
    if "user_email" not in request.session:
        return redirect("/login/")

    return render(request, "home.html", {
        "user_email": request.session.get("user_email"),
        "role": request.session.get("role", "student")
    })


# --------------------------
# Create Post (Link) - Protected
# --------------------------
# This view requires the user to be logged in.
# If the user is not logged in, they will be redirected to the login page.
def create_post_link(request):
    if "user_email" not in request.session:
        return redirect("/login/")
    return render(request, "create-post-link.html")


# --------------------------
# Create Post (Link) - Unprotected
# --------------------------
# This view allows direct access to the page without requiring the user to log in.
# If you want to make this page protected again, re-add the session check:
#     if "user_email" not in request.session:
#         return redirect("/login/")
def create_post_link(request):
    return render(request, "create-post-link.html")


# --------------------------
# Create Post (Image/Video) - Unprotected
# --------------------------
# This view allows direct access to the page without requiring the user to log in.
# To make it protected again, re-add the session check:
#     if "user_email" not in request.session:
#         return redirect("/login/")
def create_post_image(request):
    return render(request, "create-post-image.html")



# --------------------------
# Logout View
# --------------------------
def logout_page(request):
    request.session.flush()
    return redirect("/login/")
