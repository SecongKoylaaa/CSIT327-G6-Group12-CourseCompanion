from django.shortcuts import render, redirect
from supabase import create_client
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime, timezone
import uuid

# Initialize Supabase client
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)



def root_redirect(request):
    return redirect("/login/")


# --------------------------
# Registration View
# --------------------------
def register_page(request):
    if request.method == "POST":
        MAX_EMAIL_LENGTH = 50
        MAX_PASSWORD_LENGTH = 30

        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        confirm = request.POST.get("confirmPassword", "").strip()
        username = request.POST.get("username", "").strip()
        role = "student"
        profile_picture = None
        bio = None
        last_login = None

        if len(email) > MAX_EMAIL_LENGTH:
            return render(request, "register.html", {"error": f"Email cannot exceed {MAX_EMAIL_LENGTH} characters."})

        if len(password) > MAX_PASSWORD_LENGTH:
            return render(request, "register.html", {"error": f"Password cannot exceed {MAX_PASSWORD_LENGTH} characters."})

        if len(confirm) > MAX_PASSWORD_LENGTH:
            return render(request, "register.html", {"error": f"Password cannot exceed {MAX_PASSWORD_LENGTH} characters."})
        
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
        MAX_EMAIL_LENGTH = 50
        MAX_PASSWORD_LENGTH = 30

        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        if len(email) > MAX_EMAIL_LENGTH:
            return render(request, "login.html", {"error": f"Email cannot exceed {MAX_EMAIL_LENGTH} characters."})

        if len(password) > MAX_PASSWORD_LENGTH:
            return render(request, "login.html", {"error": f"Password cannot exceed {MAX_PASSWORD_LENGTH} characters."})

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

    response = supabase.table("posts").select("*").order("created_at", desc=True).execute()
    posts = response.data if response.data else []

    formatted_posts = []
    for post in posts:
        content = post.get("content", "")
        course_name = post.get("course_id") or "null"

        # Split title and URL
        if "\n" in content:
            title, url = content.split("\n", 1)
            url = url.rstrip("?")  # remove trailing '?'
        else:
            title = content
            url = ""

        # Determine if URL is an image or video
        is_image = url.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
        is_video = url.lower().endswith((".mp4", ".webm", ".ogg"))

        formatted_posts.append({
            "title": title or "(No Title)",
            "url": url,
            "created_at": time_since(post.get("created_at")),
            "author": post.get("author", "Unknown"),
            "course": f"c/{course_name}",
            "is_image": is_image,
            "is_video": is_video
        })

    return render(request, "home.html", {
        "user_email": request.session.get("user_email"),
        "role": request.session.get("role", "student"),
        "posts": formatted_posts,
    })



# Utility to convert ISO timestamp to human-readable relative time
def time_since(created_at_str):
    """Converts ISO timestamp to human-readable relative time."""
    if not created_at_str:
        return "unknown time"

    try:
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    except ValueError:
        return created_at_str

    now = datetime.now(timezone.utc)
    diff = now - created_at
    seconds = diff.total_seconds()

    if seconds < 60:
        return f"{int(seconds)}s ago"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    elif seconds < 604800:
        return f"{int(seconds // 86400)}d ago"
    elif seconds < 2419200:
        return f"{int(seconds // 604800)}w ago"
    elif seconds < 29030400:
        return f"{int(seconds // 2419200)}mo ago"
    else:
        return f"{int(seconds // 29030400)}y ago"

# --------------------------
# Create Post (Link) - Protected
# --------------------------
# This view requires the user to be logged in.
# If the user is not logged in, they will be redirected to the login page.
def create_post_link(request):
    # Require login
    if "user_email" not in request.session:
        return redirect("/login/")

    # Get user info
    user_email = request.session.get("user_email")
    user_resp = supabase.table("users").select("id").eq("email", user_email).execute()

    if not user_resp.data:
        return render(request, "create-post-link.html", {
            "error": "User not found."
        })

    user_id = user_resp.data[0]["id"]

    # Handle POST request
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        url = request.POST.get("url", "").strip()
        post_type = request.POST.get("post_type", "").strip()

        # Validate required fields
        if not title or not url or not post_type:
            return render(request, "create-post-link.html", {
                "error": "All fields are required."
            })

        # Combine title and URL into content
        content = f"{title}\n{url}"

        # Insert post record
        try:
            supabase.table("posts").insert({
                "content": content,
                "post_type": post_type,
                "user_id": user_id
            }).execute()

            return render(request, "create-post-link.html", {
                "success": "Post created successfully!"
            })

        except Exception as e:
            return render(request, "create-post-link.html", {
                "error": f"Error creating post: {str(e)}"
            })

    # Handle GET request
    return render(request, "create-post-link.html")


# --------------------------
# Create Post (Link) - Unprotected
# --------------------------
# This view allows direct access to the page without requiring the user to log in.
# If you want to make this page protected again, re-add the session check:
#     if "user_email" not in request.session:
#         return redirect("/login/")
# def create_post_link(request):
#    return render(request, "create-post-link.html")


# --------------------------
# Create Post (Image/Video) - Unprotected
# --------------------------
# This view allows direct access to the page without requiring the user to log in.
# To make it protected again, re-add the session check:
#     if "user_email" not in request.session:
#         return redirect("/login/")
def create_post_image(request):
    # Require login
    if "user_email" not in request.session:
        return redirect("/login/")

    # Get user info
    user_email = request.session.get("user_email")
    user_resp = supabase.table("users").select("id").eq("email", user_email).execute()

    if not user_resp.data:
        return render(request, "create-post-image.html", {
            "error": "User not found."
        })

    user_id = user_resp.data[0]["id"]

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        post_type = request.POST.get("post_type", "").strip()
        file = request.FILES.get("fileUpload")

        if not title or not post_type or not file:
            return render(request, "create-post-image.html", {
                "error": "All fields are required."
            })

        try:
            # Upload to Supabase Storage
            file_path = f"{user_email}/{file.name}"
            supabase.storage.from_(settings.SUPABASE_BUCKET).upload(file_path, file)
            file_url = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(file_path).rstrip("?")  # strip trailing '?'

        except Exception as e:
            return render(request, "create-post-image.html", {
                "error": f"File upload failed: {str(e)}"
            })

        # Combine title and file URL
        content = f"{title}\n{file_url}"

        try:
            supabase.table("posts").insert({
                "content": content,
                "post_type": post_type,
                "user_id": user_id
            }).execute()

            return render(request, "create-post-image.html", {
                "success": "Post created successfully!"
            })

        except Exception as e:
            return render(request, "create-post-image.html", {
                "error": f"Error creating post: {str(e)}"
            })

    return render(request, "create-post-image.html")


# --------------------------
# Logout View
# --------------------------
def logout_page(request):
    request.session.flush()
    return redirect("/login/")
