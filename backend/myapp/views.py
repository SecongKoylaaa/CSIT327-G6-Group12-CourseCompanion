from django.shortcuts import render, redirect
from django.utils import timezone
from supabase import create_client
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime, timedelta  # <-- add this line
from myapp.models import *
import secrets
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
        confirm_password = request.POST.get("confirmPassword", "").strip()
        username = request.POST.get("username", "").strip()
        role = request.POST.get("role", "").strip().lower()

        if not email or not password or not confirm_password or not role:
            return render(request, "register.html", {"error": "All fields are required."})

        if password != confirm_password:
            return render(request, "register.html", {"error": "Passwords do not match."})

        if role not in ["student", "teacher"]:
            return render(request, "register.html", {"error": "Invalid role selected."})

        # Check if user exists
        if User.objects.filter(email=email).exists():
            return render(request, "register.html", {"error": "Account already exists. Please login."})

        # Create user
        user = User(
            email=email,
            password_hash=make_password(password),
            username=username if username else None,
            role=role,
            date_joined=timezone.now(),
            last_login=None,
            bio=None,
            profile_picture=None,
        )
        user.save()

        return redirect("/login/")

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
            user = User.objects.filter(email=email).first()
        except Exception as e:
            return render(request, "login.html", {"error": f"Database error: {str(e)}"})

        if not user:
            return render(request, "login.html", {"error": "No account found. Please register."})

        if not check_password(password, user.password_hash):
            return render(request, "login.html", {"error": "Invalid credentials!"})

        # ✅ Save user session
        request.session["user_email"] = user.email
        request.session["role"] = user.role

        # ✅ Update last_login timestamp
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        return redirect("/home/")

    return render(request, "login.html")

# --------------------------
# Password Recovery View
# --------------------------    
def recover_password_page(request):
    email = ""

    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not email:
            return render(request, "recover_password.html", {
                "error": "Email is required.",
                "email": email
            })

        # ✅ Check if user exists
        try:
            user = User.objects.filter(email=email).first()
        except Exception as e:
            return render(request, "recover_password.html", {
                "error": f"Database error: {str(e)}",
                "email": email
            })

        if not user:
            return render(request, "recover_password.html", {
                "error": "No account found with that email.",
                "email": email
            })

        # ✅ Generate token and expiration
        reset_token = secrets.token_urlsafe(32)
        expiration_time = timezone.now() + timedelta(hours=1)

        # ✅ Store in PasswordRecovery table
        try:
            PasswordRecovery.objects.create(
                reset_token=reset_token,
                expiration_time=expiration_time,
                user=user,
                created_at=timezone.now()
            )
        except Exception as e:
            return render(request, "recover_password.html", {
                "error": f"Error saving reset token: {str(e)}",
                "email": email
            })

        # ✅ Show test link (in production, you'd send email instead)
        reset_link = f"/reset-password/{reset_token}/"

        return render(request, "recover_password.html", {
            "message": "If this email exists, a recovery link has been generated.",
            "email": email,
            "reset_link": reset_link
        })

    return render(request, "recover_password.html", {"email": email})

# --------------------------
# Password Reset View
# --------------------------
def reset_password_page(request, reset_token):
    # ✅ Look up the token in PasswordRecovery
    try:
        token_entry = PasswordRecovery.objects.select_related(None).filter(reset_token=reset_token).first()
    except Exception as e:
        return render(request, "reset_password.html", {"error": f"Error looking up token: {str(e)}"})

    if not token_entry:
        return render(request, "reset_password.html", {"error": "Invalid or expired reset token."})

    # ✅ Check expiration
    expiration_time = token_entry.expiration_time
    if not expiration_time:
        return render(request, "reset_password.html", {"error": "Token missing expiration."})

    if expiration_time < timezone.now():
        return render(request, "reset_password.html", {"error": "Reset token has expired."})

    # ✅ Handle password reset form
    if request.method == "POST":
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if not new_password or not confirm_password:
            return render(request, "reset_password.html", {
                "error": "All fields are required.",
                "reset_token": reset_token
            })

        if new_password != confirm_password:
            return render(request, "reset_password.html", {
                "error": "Passwords do not match.",
                "reset_token": reset_token
            })

        user = getattr(token_entry, "user", None)
        if not user:
            return render(request, "reset_password.html", {"error": "User not found for this token.", "reset_token": reset_token})

        # ✅ Prevent using same password
        if check_password(new_password, user.password_hash):
            return render(request, "reset_password.html", {"error": "You cannot use your old password.", "reset_token": reset_token})

        # ✅ Update password
        try:
            user.password_hash = make_password(new_password)
            user.save(update_fields=["password_hash"])
        except Exception as e:
            return render(request, "reset_password.html", {"error": f"Error updating password: {str(e)}", "reset_token": reset_token})

        # ✅ Delete used token
        try:
            token_entry.delete()
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

    posts = Post.objects.select_related("course", "user").order_by("-created_at")

    formatted_posts = []
    for post in posts:
        url = (post.content or "").rstrip("?")
        is_image = url.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
        is_video = url.lower().endswith((".mp4", ".webm", ".ogg"))

        formatted_posts.append({
            "title": post.title or "(No Title)",
            "url": url,
            "description": post.description or "",
            "created_at": time_since(post.created_at),
            "author": post.user.username if post.user else "Unknown",
            "course": f"c/{post.course.course_name}" if post.course else "null",
            "is_image": is_image,
            "is_video": is_video,
        })

    return render(request, "home.html", {
        "user_email": request.session.get("user_email"),
        "role": request.session.get("role", "student"),
        "posts": formatted_posts,
    })


# Utility to convert ISO timestamp to human-readable relative time
def time_since(created_at):
    """Returns a compact, social-style timestamp like '3m ago' or 'Just now'."""
    if not created_at:
        return "unknown time"

    # Convert ISO string → datetime if needed
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except Exception:
            return created_at

    # Ensure timezone awareness
    if timezone.is_naive(created_at):
        created_at = timezone.make_aware(created_at, timezone=timezone.utc)

    now = timezone.now()
    diff = now - created_at
    seconds = int(diff.total_seconds())

    if seconds < 10:
        return "Just now"
    elif seconds < 60:
        return f"{seconds}s ago"
    elif seconds < 3600:
        return f"{seconds // 60}m ago"
    elif seconds < 86400:
        return f"{seconds // 3600}h ago"
    elif seconds < 604800:
        return f"{seconds // 86400}d ago"
    elif seconds < 2419200:
        return f"{seconds // 604800}w ago"
    elif seconds < 29030400:
        return f"{seconds // 2419200}mo ago"
    else:
        return f"{seconds // 29030400}y ago"


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
    # Require login
    if "user_email" not in request.session:
        return redirect("/login/")

    # Get user info
    user_email = request.session.get("user_email")
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        return render(request, "create-post-link.html", {
            "error": "User not found."
        })

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        post_type = request.POST.get("post_type", "").strip()
        url = request.POST.get("url", "").strip()

        # Validate
        if not title or not description or not post_type or not url:
            return render(request, "create-post-link.html", {
                "error": "All fields are required."
            })

        try:
            # Insert using Django ORM
            Post.objects.create(
                title=title,
                description=description,
                post_type=post_type,
                content=url,
                user=user,
                created_at=timezone.now()
            )

            return render(request, "create-post-link.html", {
                "success": "Post created successfully!"
            })

        except Exception as e:
            return render(request, "create-post-link.html", {
                "error": f"Error creating post: {str(e)}"
            })

    return render(request, "create-post-link.html")



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
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        return render(request, "create-post-image.html", {
            "error": "User not found."
        })

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        post_type = request.POST.get("post_type", "").strip()
        file = request.FILES.get("fileUpload")

        # Validate required fields
        if not title or not description or not post_type or not file:
            return render(request, "create-post-image.html", {
                "error": "All fields are required."
            })

        try:
            # Upload file to Supabase Storage
            file_path = f"{user_email}/{file.name}"
            file_bytes = file.read()  # Convert InMemoryUploadedFile to bytes
            supabase.storage.from_(settings.SUPABASE_BUCKET).upload(file_path, file_bytes)

            # Get public URL
            file_url = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(file_path).rstrip("?")

        except Exception as e:
            return render(request, "create-post-image.html", {
                "error": f"File upload failed: {str(e)}"
            })

        try:
            # Insert post record using Django ORM
            Post.objects.create(
                title=title,
                description=description,
                content=file_url,
                post_type=post_type,
                user=user,
                created_at=timezone.now()
            )

            return render(request, "create-post-image.html", {
                "success": "Post created successfully!"
            })

        except Exception as e:
            return render(request, "create-post-image.html", {
                "error": f"Error creating post: {str(e)}"
            })

    # GET request
    return render(request, "create-post-image.html")




# --------------------------
# Logout View
# --------------------------
def logout_page(request):
    request.session.flush()
    return redirect("/login/")
