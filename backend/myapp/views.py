from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime, timezone, timedelta
from supabase import create_client
from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Post
from .forms import PostForm
import time
import secrets
import os

# --------------------------
# Initialize Supabase client (use service role if available)
SUPABASE_AUTH_KEY = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None) or settings.SUPABASE_KEY
supabase = create_client(settings.SUPABASE_URL, SUPABASE_AUTH_KEY)

# Available academic subjects used across post creation and communities
SUBJECTS = [
    "Filipino",
    "Math",
    "Araling Panlipunan",
    "English",
    "Science",
    "Physics",
    "Chemistry",
    "Biology",
    "History",
    "Geography",
    "Edukasyon sa Pagpapakatao",
    "Economics",
    "Technology and Home Economics",
    "Integrated Science",
    "Health",
    "Music",
    "Art",
    "Physical Education",
]

# --------------------------
# Utility: Safe Supabase execute with retries
# --------------------------
def safe_execute(request_fn, retries=3, delay=0.1):
    """Execute Supabase request with automatic retries on transient errors."""
    last_exception = None
    for attempt in range(retries):
        try:
            return request_fn()
        except Exception as e:
            last_exception = e
            error_str = str(e).lower()
            error_type = type(e).__name__
            
            # Retry on transient network/connection errors
            if any(keyword in error_str for keyword in ["non-blocking socket", "server disconnected", "connection", "timeout"]) \
               or any(err_type in error_type for err_type in ["RemoteProtocolError", "ConnectionError", "TimeoutError"]):
                if attempt < retries - 1:  # Don't sleep on last attempt
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
                    continue
            # Non-transient error, raise immediately
            raise
    # All retries exhausted, raise last exception
    if last_exception:
        raise last_exception
    return request_fn()

# --------------------------
# Root: splash / landing page
# --------------------------
def root_redirect(request):
    return render(request, "splash_page.html")

# --------------------------
# Helper: Fetch profile picture URL for navbar
# --------------------------
def get_profile_picture_url(request):
    email = request.session.get("user_email")
    if not email:
        return None
    try:
        resp = safe_execute(lambda: supabase.table("users").select("profile_picture").eq("email", email).maybe_single().execute())
        return resp.data.get("profile_picture") if resp and resp.data else None
    except Exception:
        return None

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

        # Check for admin credentials first
        if email == "admin@gmail.com" and password == "admin123#password":
            request.session["user_email"] = email
            request.session["role"] = "admin"
            return redirect("/dashboard/")

        try:
            response = safe_execute(lambda: supabase.table("users").select("*").eq("email", email).execute())
        except Exception as e:
            return render(request, "login.html", {"error": f"Error connecting to database: {str(e)}"})

        if not response.data:
            return render(request, "login.html", {"error": "No account found. Please register."})

        user = response.data[0]
        if not check_password(password, user["password_hash"]):
            return render(request, "login.html", {"error": "Invalid credentials!"})

        request.session["user_email"] = email
        request.session["role"] = user.get("role", "student")

        try:
            supabase.table("users").update({
                "last_login": datetime.now(timezone.utc).isoformat()
            }).eq("email", email).execute()
        except Exception:
            pass

        return redirect("/home/")

    return render(request, "login.html", {
        "profile_picture_url": get_profile_picture_url(request)
    })

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

        # Validation
        if not email or not password or not confirm:
            return render(request, "register.html", {"error": "All fields are required."})
        if len(email) > MAX_EMAIL_LENGTH:
            return render(request, "register.html", {"error": "Email is too long."})
        if len(password) > MAX_PASSWORD_LENGTH:
            return render(request, "register.html", {"error": "Password is too long."})
        if password != confirm:
            return render(request, "register.html", {"error": "Passwords do not match."})

        # Check if email exists
        try:
            existing = safe_execute(lambda: supabase.table("users").select("*").eq("email", email).execute())
            if existing.data:
                return render(request, "register.html", {"error": "Account already exists. Please login."})
        except Exception as e:
            return render(request, "register.html", {"error": f"Database error: {str(e)}"})

        # Insert User
        password_hash = make_password(password)
        date_joined = datetime.now(timezone.utc).isoformat()
        try:
            response = safe_execute(lambda: supabase.table("users").insert({
                "email": email,
                "password_hash": password_hash,
                "username": None,
                "role": "student",
                "profile_picture": None,
                "bio": None,
                "last_login": None,
                "date_joined": date_joined
            }).execute())
            if getattr(response, "error", None):
                return render(request, "register.html", {"error": f"Error registering: {response.error}"})
        except Exception as e:
            return render(request, "register.html", {"error": f"Error registering: {str(e)}"})

        return redirect("/login/")

    return render(request, "register.html", {
        "profile_picture_url": get_profile_picture_url(request)
    })

# --------------------------
# Password Recovery View
# --------------------------
def recover_password_page(request):
    email = ""
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if not email:
            return render(request, "recover_password.html", {"error": "Email is required.", "email": email})

        # Check if user exists
        try:
                response = safe_execute(lambda: supabase.table("users").select("*").eq("email", email).execute())
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
        return render(request, "recover_password.html", {
            "error": None,
            "message": "If this email exists, a recovery link has been generated.",
            "email": email,
            "reset_link": reset_link,
            "profile_picture_url": get_profile_picture_url(request)
        })

    return render(request, "recover_password.html", {
        "email": email,
        "profile_picture_url": get_profile_picture_url(request)
    })

# --------------------------
# Password Reset View
# --------------------------
def reset_password_page(request, reset_token):
    # Lookup token in password_recovery
    try:
        token_resp = supabase.table("password_recovery") \
            .select("*", count="exact") \
            .eq("reset_token", reset_token) \
            .execute()
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

    # Handle POST request for resetting password
    if request.method == "POST":
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if not new_password or not confirm_password:
            return render(request, "reset_password.html", {"error": "All fields are required.", "reset_token": reset_token})

        if new_password != confirm_password:
            return render(request, "reset_password.html", {"error": "Passwords do not match.", "reset_token": reset_token})

        user_id = token_row.get("user_id") or token_row.get("id")
        if not user_id:
            return render(request, "reset_password.html", {"error": "User not found for this token.", "reset_token": reset_token})

        # Fetch current password hash
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

        # Update user's password
        password_hash = make_password(new_password)
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

        return render(request, "reset_password.html", {
            "message": "Password reset successful! You can now log in.",
            "profile_picture_url": get_profile_picture_url(request)
        })

    return render(request, "reset_password.html", {
        "reset_token": reset_token,
        "profile_picture_url": get_profile_picture_url(request)
    })

# -----------------------------
# Helper: parse datetime string
# -----------------------------
def parse_datetime(dt_str):
    """Convert ISO string from Supabase to datetime object."""
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)

# -----------------------------
# Helper: build nested comment tree
# -----------------------------
def build_comment_tree(comments, parent_id_val=None, user_id=None):
    """
    Recursively build a nested comment tree with votes and per-user states.
    """
    tree = []
    for c in comments:
        if c.get("parent_id") == parent_id_val:
            # Get author email (retry on transient disconnects)
            user_resp = safe_execute(lambda: supabase.table("users").select("email").eq("id", c["user_id"]).maybe_single().execute())
            author_email = user_resp.data["email"] if user_resp.data and "email" in user_resp.data else "anonymous@example.com"

            # Fetch votes (retry on transient disconnects)
            votes_resp = safe_execute(lambda: supabase.table("comment_votes").select("*").eq("comment_id", c["comment_id"]).execute())
            votes = votes_resp.data or []

            upvotes = len([v for v in votes if v["vote_type"] == "upvote"])
            downvotes = len([v for v in votes if v["vote_type"] == "downvote"])
            net_votes = upvotes - downvotes

            # Determine current user's vote properly
            raw_vote = next((v["vote_type"] for v in votes if v["user_id"] == user_id), None)
            if raw_vote == "upvote":
                user_vote = "upvote"
            elif raw_vote == "downvote":
                user_vote = "downvote"
            else:
                user_vote = None

            # Build comment object
            comment_obj = {
                "comment_id": c["comment_id"],
                "author": author_email,
                "text": c["text"],
                "created_at": parse_datetime(c.get("created_at")),
                "edited": c.get("edited", False),
                "upvote_count": upvotes,
                "downvote_count": downvotes,
                "net_votes": net_votes,
                "user_vote": user_vote,
                "replies": build_comment_tree(comments, parent_id_val=c["comment_id"], user_id=user_id)
            }
            tree.append(comment_obj)
    return tree

# -----------------------------
# Home page view
# -----------------------------
def home_page(request):
    if "user_email" not in request.session:
        return redirect("/login/")
    try:
        user_email = request.session.get("user_email")
        # Wrap Supabase calls with retries to avoid transient disconnects
        user_resp = safe_execute(lambda: supabase.table("users").select("*").eq("email", user_email).maybe_single().execute())
        profile_picture_url = user_resp.data["profile_picture"] if user_resp.data and user_resp.data.get("profile_picture") else None
    except Exception:
        # Graceful banner if a transient crash occurs; user doesn't need to refresh
        request.session["success_message"] = "We hit a brief connection hiccup and auto-retried."
        profile_picture_url = None

    # Optional subject filter from query string or POST (for comment submissions)
    selected_subject = request.GET.get("subject") or request.POST.get("subject") or None
    
    # Optional search query from navbar
    search_query = request.GET.get("search", "").strip()

    # -----------------------------
    # Handle new comment or reply
    # -----------------------------
    if request.method == "POST":
        post_id = request.POST.get("post_id")
        comment_text = request.POST.get("comment")
        parent_id = request.POST.get("parent_id")

        # Get user_id
        user_resp = safe_execute(lambda: supabase.table("users").select("id").eq("email", user_email).maybe_single().execute())
        user_id = user_resp.data["id"] if user_resp.data else None

        if post_id and comment_text and user_id:
            safe_execute(lambda: supabase.table("comments").insert({
                "post_id": post_id,
                "user_id": user_id,
                "parent_id": parent_id,
                "text": comment_text,
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute())

        # Redirect back to the same subject view if available
        if selected_subject:
            return redirect(f"/home/?subject={selected_subject}")
        return redirect("/home/")

    # -----------------------------
    # Fetch posts (optionally filtered by subject and/or search) with pagination
    # -----------------------------
    page_size = 15
    try:
        page = int(request.GET.get("page", "1"))
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    start = (page - 1) * page_size
    end = start + page_size - 1

    posts_query = supabase.table("posts").select("*")
    if selected_subject:
        posts_query = posts_query.eq("subject", selected_subject)
    
    # Apply search filter if query exists
    if search_query:
        posts_query = posts_query.ilike("title", f"%{search_query}%")

    response = safe_execute(lambda: posts_query.order("created_at", desc=True).range(start, end).execute())
    posts = response.data if response.data else []

    # Get current user ID for vote detection
    user_id = None
    if user_email:
        user_resp = safe_execute(lambda: supabase.table("users").select("id").eq("email", user_email).maybe_single().execute())
        if user_resp.data:
            user_id = user_resp.data["id"]
    # Removed debug print for cleanliness


    formatted_posts = []

    for post in posts:
        title = post.get("title") or "(No Title)"
        url = post.get("content", "").rstrip("?")
        course_name = post.get("subject") or "General"
        description = post.get("description", "")
        post_id = post.get("post_id")
        author_id = post.get("user_id")

        is_image = url.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"))
        is_video = url.lower().endswith((".mp4", ".webm", ".ogg"))

        # Fetch author username and email for display
        author_display = "anonymous"
        author_username = None
        author_email = None
        if author_id:
            author_resp = safe_execute(lambda: supabase.table("users").select("username, email").eq("id", author_id).maybe_single().execute())
            if author_resp.data:
                author_username = author_resp.data.get("username")
                author_email = author_resp.data.get("email")
                # Use username if available, otherwise use email
                author_display = author_username if author_username else (author_email or "anonymous")

        # -----------------------------
        # Fetch votes for this post
        # -----------------------------
        votes_resp = safe_execute(lambda: supabase.table("post_votes").select("*").eq("post_id", post_id).execute())
        votes = votes_resp.data or []

        upvotes = len([v for v in votes if v["vote_type"] == "up"])
        downvotes = len([v for v in votes if v["vote_type"] == "down"])
        net_votes = upvotes - downvotes

        user_vote = None
        if user_id:
            uv = next((v["vote_type"] for v in votes if v["user_id"] == user_id), None)
            if uv == "up":
                user_vote = "upvote"
            elif uv == "down":
                user_vote = "downvote"
            else:
                user_vote = None


        # -----------------------------
        # Defer comments: loaded on demand via AJAX
        nested_comments = []

        formatted_posts.append({
            "id": post_id,
            "title": title,
            "url": url,
            "description": description,
            "created_at": time_since(post.get("created_at")),
            "author": author_display,
            "course": course_name,
            "is_image": is_image,
            "is_video": is_video,
            "comments": nested_comments,
                "upvote_count": upvotes,
            "vote_count": net_votes,
            "user_vote": user_vote,
            # comment_count fetched lazily (approximate from table)
            "comment_count": safe_execute(lambda: supabase.table("comments").select("comment_id", count="exact").eq("post_id", post_id).execute()).count or 0,
            # owner of the post, used to control author-only UI (3-dots menu)
            "user_id": author_id,
        })

    # Pull and clear any success message (e.g., from profile edit)
    success_message = request.session.pop("success_message", None)

    return render(request, "home.html", {
        "user_email": user_email,
        "role": request.session.get("role", "student"),
        "posts": formatted_posts,
        "profile_picture_url": profile_picture_url,  # unchanged
        "success": success_message,
        # current logged-in user's id, used in template for author-only controls
        "current_user_id": user_id,
        # Communities / subjects sidebar data
        "subjects": SUBJECTS,
        "selected_subject": selected_subject,
        # search query for navbar persistence
        "search_query": search_query,
        # pagination controls
        "page": page,
        "has_next": len(posts) == page_size,
        "has_prev": page > 1,
    })

# -----------------------------
# AJAX: Load comments for a post on demand
# -----------------------------
@csrf_exempt
def comments_for_post(request, post_id):
    if request.method != "GET":
        return HttpResponseForbidden("Invalid method")

    user_email = request.session.get("user_email")
    user_id = None
    if user_email:
        user_resp = safe_execute(lambda: supabase.table("users").select("id").eq("email", user_email).maybe_single().execute())
        if user_resp.data:
            user_id = user_resp.data["id"]

    comment_resp = safe_execute(lambda: supabase.table("comments").select("*").eq("post_id", post_id).order("created_at", desc=False).execute())
    all_comments = comment_resp.data if comment_resp.data else []

    seen_cids = set()
    seen_composite = set()
    dedup_comments = []
    for c in all_comments:
        cid = c.get("comment_id")
        pid = c.get("post_id")
        txt = (c.get("text") or "").strip()
        created = (c.get("created_at") or "")
        created_key = created[:19] if isinstance(created, str) else str(created)[:19]
        comp = (pid, txt, created_key)
        if cid:
            if cid in seen_cids or comp in seen_composite:
                continue
            seen_cids.add(cid)
            seen_composite.add(comp)
            dedup_comments.append(c)
        else:
            if comp in seen_composite:
                continue
            seen_composite.add(comp)
            dedup_comments.append(c)

    nested = build_comment_tree(dedup_comments, user_id=user_id)

    post_ctx = {
        "id": post_id,
        "comments": nested
    }
    # Include selected_subject and render with request to inject CSRF token
    selected_subject = request.GET.get("subject") or None
    html = render_to_string(
        "comments.html",
        {"post": post_ctx, "selected_subject": selected_subject, "user_email": user_email},
        request=request,
    )
    return HttpResponse(html)

# --------------------------
# Comment Editing & Deletion
# --------------------------
def edit_comment(request, comment_id):
    if request.method != "POST":
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # Fetch comment
    resp = safe_execute(lambda: supabase.table("comments").select("*").eq("comment_id", comment_id).maybe_single().execute())
    comment = resp.data
    if not comment:
        return HttpResponseForbidden("Comment not found.")

    # Get current user
    user_email = request.session.get("user_email")
    user_resp = safe_execute(lambda: supabase.table("users").select("id").eq("email", user_email).maybe_single().execute())
    user_id = user_resp.data["id"] if user_resp.data else None

    if comment["user_id"] != user_id:
        return HttpResponseForbidden("You can't edit this comment.")

    # Update comment
    safe_execute(lambda: supabase.table("comments").update({
        "text": request.POST.get("comment"),
        "edited": True
    }).eq("comment_id", comment_id).execute())

    return redirect(request.META.get('HTTP_REFERER', '/'))


def delete_comment(request, comment_id):
    if request.method != "POST":
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # Fetch comment
    resp = safe_execute(lambda: supabase.table("comments").select("*").eq("comment_id", comment_id).maybe_single().execute())
    comment = resp.data
    if not comment:
        return HttpResponseForbidden("Comment not found.")

    # Get current user
    user_email = request.session.get("user_email")
    user_resp = safe_execute(lambda: supabase.table("users").select("id").eq("email", user_email).maybe_single().execute())
    user_id = user_resp.data["id"] if user_resp.data else None

    if comment["user_id"] != user_id:
        return HttpResponseForbidden("You can't delete this comment.")

    # Delete comment
    safe_execute(lambda: supabase.table("comments").delete().eq("comment_id", comment_id).execute())
    return redirect(request.META.get('HTTP_REFERER', '/'))


@csrf_exempt
def report_comment(request):
    """Handle comment reporting. Stores into comment_reports for admin review later."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    user_email = request.session.get('user_email')
    if not user_email:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        # Get reporting user ID
        user_resp = supabase.table('users').select('id').eq('email', user_email).maybe_single().execute()
        if not user_resp.data:
            return JsonResponse({'error': 'User not found'}, status=404)
        user_id = user_resp.data['id']

        comment_id = request.POST.get('comment_id')
        violation_type = request.POST.get('violation_type') or 'other'
        details = (request.POST.get('details', '') or '').strip()

        if not comment_id:
            return JsonResponse({'error': 'Missing comment_id'}, status=400)

        # Store violation code and user description in dedicated columns
        reason = violation_type
        description = details

        supabase.table('comment_reports').insert({
            'comment_id': int(comment_id),
            'reporter_id': user_id,
            'reason': reason,
            'description': description
        }).execute()

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# --------------------------
# Comment Voting
# --------------------------
@csrf_exempt
def vote_comment(request, comment_id, vote_type):
    if "user_email" not in request.session:
        return JsonResponse({"error": "Login required"}, status=403)

    user_email = request.session.get("user_email")

    # Fetch user ID safely
    user_resp = safe_execute(lambda: supabase.table("users").select("id").eq("email", user_email).maybe_single().execute())
    if not user_resp or not user_resp.data:
        return JsonResponse({"error": "User not found"}, status=404)

    user_id = user_resp.data["id"]

    # Check if vote exists for this user/comment
    existing_vote_resp = safe_execute(lambda: supabase.table("comment_votes") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("comment_id", comment_id) \
        .maybe_single() \
        .execute())

    existing_vote = existing_vote_resp.data if existing_vote_resp and existing_vote_resp.data else None

    # Process voting logic
    if existing_vote:
        if existing_vote["vote_type"] == vote_type:
            # Same vote again → remove it (unvote)
            safe_execute(lambda: supabase.table("comment_votes").delete().eq("vote_id", existing_vote["vote_id"]).execute())
            message = "Vote removed"
        else:
            # Switch vote type
            safe_execute(lambda: supabase.table("comment_votes").update({"vote_type": vote_type}).eq("vote_id", existing_vote["vote_id"]).execute())
            message = "Vote updated"
    else:
        # New vote
        safe_execute(lambda: supabase.table("comment_votes").insert({
            "user_id": user_id,
            "comment_id": comment_id,
            "vote_type": vote_type
        }).execute())
        message = "Vote added"

    # Get updated totals
    votes_resp = safe_execute(lambda: supabase.table("comment_votes") \
        .select("vote_type") \
        .eq("comment_id", comment_id) \
        .execute())

    if not votes_resp or votes_resp.data is None:
        total_votes = 0
    else:
        total_votes = sum(1 if v["vote_type"] == "upvote" else -1 for v in votes_resp.data)

    return JsonResponse({
        "message": message,
        "net_votes": total_votes,  # ✅ must match frontend key
        "user_vote": vote_type if message != "Vote removed" else None
    })

# --------------------------
# Post Voting
# --------------------------
@csrf_exempt
def vote_post(request, post_id, vote_type):
    if "user_email" not in request.session:
        return JsonResponse({"error": "Login required"}, status=403)

    user_email = request.session.get("user_email")

    # Fetch user ID
    user_resp = safe_execute(lambda: supabase.table("users").select("id").eq("email", user_email).maybe_single().execute())
    if not user_resp or not user_resp.data:
        return JsonResponse({"error": "User not found"}, status=404)

    user_id = user_resp.data["id"]

    # Check existing vote
    existing_vote_resp = safe_execute(lambda: supabase.table("post_votes") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("post_id", post_id) \
        .maybe_single() \
        .execute())

    existing_vote = existing_vote_resp.data if existing_vote_resp and existing_vote_resp.data else None

    # Process voting
    if existing_vote:
        if existing_vote["vote_type"] == vote_type:
            # Same vote → remove
            safe_execute(lambda: supabase.table("post_votes") \
                .delete() \
                .eq("vote_id", existing_vote["vote_id"]) \
                .execute())
            message = "Vote removed"
        else:
            # Switch vote
            safe_execute(lambda: supabase.table("post_votes") \
                .update({"vote_type": vote_type}) \
                .eq("vote_id", existing_vote["vote_id"]) \
                .execute())
            message = "Vote updated"
    else:
        # New vote
        safe_execute(lambda: supabase.table("post_votes").insert({
            "user_id": user_id,
            "post_id": post_id,
            "vote_type": vote_type
        }).execute())
        message = "Vote added"

    # ---- FIX: Read updated counts from posts table ----
    post_resp = safe_execute(lambda: supabase.table("posts") \
        .select("upvote_count, downvote_count") \
        .eq("post_id", post_id) \
        .maybe_single() \
        .execute())

    if not post_resp or not post_resp.data:
        return JsonResponse({"error": "Post not found after vote"}, status=404)

    upvotes = post_resp.data["upvote_count"]
    downvotes = post_resp.data["downvote_count"]
    net_votes = upvotes - downvotes

    return JsonResponse({
        "message": message,
        "net_votes": net_votes,
        "upvotes": upvotes,
        "downvotes": downvotes,
        "user_vote": vote_type if message != "Vote removed" else None
    })


# --------------------------
# Utility: Human-readable time
# --------------------------
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
    seconds = max(diff.total_seconds(), 0)

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


FRONTEND_TO_DB = {
    "upvote": "up",
    "downvote": "down"
}

@csrf_exempt
def vote_post(request, post_id, vote_type):
    if "user_email" not in request.session:
        return JsonResponse({"error": "Login required"}, status=403)

    user_email = request.session.get("user_email")

    # Get user ID
    user_resp = safe_execute(lambda: supabase.table("users").select("id").eq("email", user_email).maybe_single().execute())
    if not user_resp.data:
        return JsonResponse({"error": "User not found"}, status=404)
    user_id = user_resp.data["id"]

    # Validate vote type
    if vote_type not in FRONTEND_TO_DB:
        return JsonResponse({"error": "Invalid vote type"}, status=400)
    db_vote_value = FRONTEND_TO_DB[vote_type]

    # Check if post exists
    post_resp = safe_execute(lambda: supabase.table("posts").select("post_id").eq("post_id", post_id).maybe_single().execute())
    if not post_resp.data:
        return JsonResponse({"error": "Post not found"}, status=404)

    # Check for existing vote
    existing_vote_resp = safe_execute(lambda: supabase.table("post_votes")\
        .select("*")\
        .eq("post_id", post_id)\
        .eq("user_id", user_id)\
        .maybe_single()\
        .execute())
    existing_vote = existing_vote_resp.data if existing_vote_resp and existing_vote_resp.data else None

    user_vote = None

    if existing_vote:
        if existing_vote.get("vote_type") == db_vote_value:
            # Same vote again → remove vote
            safe_execute(lambda: supabase.table("post_votes").delete().eq("vote_id", existing_vote["vote_id"]).execute())
        else:
            # Change vote type
            safe_execute(lambda: supabase.table("post_votes").update({"vote_type": db_vote_value}).eq("vote_id", existing_vote["vote_id"]).execute())
            user_vote = vote_type
    else:
        # Insert new vote safely
        try:
            safe_execute(lambda: supabase.table("post_votes").insert({
                "user_id": user_id,
                "post_id": post_id,
                "vote_type": db_vote_value
            }).execute())
            user_vote = vote_type
        except Exception as e:
            if "duplicate key value" in str(e):
                # Handle race condition / duplicate insert
                existing_vote_resp = safe_execute(lambda: supabase.table("post_votes")\
                    .select("*")\
                    .eq("post_id", post_id)\
                    .eq("user_id", user_id)\
                    .maybe_single()\
                    .execute())
                existing_vote = existing_vote_resp.data
                if existing_vote:
                    safe_execute(lambda: supabase.table("post_votes")\
                        .update({"vote_type": db_vote_value})\
                        .eq("vote_id", existing_vote["vote_id"])\
                        .execute())
                    user_vote = vote_type
            else:
                raise e

    # Compute net votes
    votes_resp = safe_execute(lambda: supabase.table("post_votes").select("vote_type").eq("post_id", post_id).execute())
    votes = votes_resp.data or []
    net_votes = sum(1 if v.get("vote_type") == "up" else -1 for v in votes)

    return JsonResponse({
        "net_votes": net_votes,
        "user_vote": user_vote
    })

# --------------------------
# Create Post - Text
# --------------------------
def create_post_text(request):
    if "user_email" not in request.session:
        return redirect("/login/")

    user_email = request.session.get("user_email")
    # FIX: fetch profile_picture as well
    user_resp = supabase.table("users").select("id, profile_picture").eq("email", user_email).maybe_single().execute()
    if not user_resp.data:
        return render(request, "create-post-text.html", {"error": "User not found."})
    user_data = user_resp.data
    user_id = user_data["id"]
    profile_picture_url = user_data.get("profile_picture")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        post_type = request.POST.get("post_type", "").strip()
        subject = request.POST.get("subject", "").strip()

        # Enforce max lengths
        if len(title) > 300:
            title = title[:300]
        if len(description) > 1000:
            description = description[:1000]

        # Validate
        if not title or not description or not post_type or not subject:
            return render(request, "create-post-text.html", {
                "error": "All fields are required.",
                "title": title,
                "description": description,
                "post_type": post_type,
                "subject": subject
            })

        # Insert post
        try:
            supabase.table("posts").insert({
                "title": title,
                "description": description,
                "content": "",
                "post_type": post_type,
                "user_id": user_id,
                "subject": subject
            }).execute()

            return render(request, "create-post-text.html", {
                "success": "Post created successfully!",
                "title": "",
                "description": "",
                "post_type": "",
                "subject": ""
            })

        except Exception as e:
            return render(request, "create-post-text.html", {
                "error": f"Error creating post: {str(e)}",
                "title": title,
                "description": description,
                "post_type": post_type,
                "subject": subject
            })

    return render(request, "create-post-text.html", {
        "profile_picture_url": profile_picture_url
    })

# --------------------------
# Create Post - Image/Video
# --------------------------
def create_post_image(request):
    if "user_email" not in request.session:
        return redirect("/login/")

    # Get user
    user_email = request.session.get("user_email")
    # FIX: fetch profile_picture as well
    user_resp = supabase.table("users").select("id, profile_picture").eq("email", user_email).maybe_single().execute()
    if not user_resp.data:
        return render(request, "create-post-text.html", {"error": "User not found."})
    user_data = user_resp.data
    user_id = user_data["id"]
    profile_picture_url = user_data.get("profile_picture")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        post_type = request.POST.get("post_type", "").strip()
        subject = request.POST.get("subject", "").strip()   # changed from course → subject
        uploaded_file = request.FILES.get("fileUpload")

        # Validate
        if not title or not post_type or not subject or not uploaded_file:
            return render(request, "create-post-image-video.html", {
                "error": "All fields are required.",
                "title": title,
                "description": description,
                "post_type": post_type,
                "subject": subject,
            })

        # Upload file to Supabase Storage (reuse existing if duplicate)
        try:
            file_path = f"{user_email}/{uploaded_file.name}"
            file_bytes = uploaded_file.read()

            # Try to upload; allow upsert so duplicate names are reused
            try:
                supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                    file_path,
                    file_bytes,
                    file_options={"contentType": uploaded_file.content_type or "application/octet-stream", "upsert": "true"}
                )
            except Exception as up_err:
                # If duplicate, still proceed by using existing public URL
                msg = str(up_err).lower()
                if "409" in msg or "duplicate" in msg or "already exists" in msg:
                    pass  # safe to ignore and reuse existing file
                else:
                    raise up_err

            file_url = supabase.storage.from_(settings.SUPABASE_BUCKET)\
                        .get_public_url(file_path)\
                        .split("?")[0]

        except Exception as e:
            return render(request, "create-post-image-video.html", {
                "error": f"File upload failed: {str(e)}",
                "title": title,
                "description": description,
                "post_type": post_type,
                "subject": subject,
            })

        # Insert post record
        try:
            supabase.table("posts").insert({
                "title": title,
                "description": description,
                "content": file_url,
                "post_type": post_type,
                "subject": subject,       # SAVE SUBJECT HERE
                "user_id": user_id
            }).execute()

            preview_type = "video" if uploaded_file.content_type.startswith("video") else "image"

            return render(request, "create-post-image-video.html", {
                "success": "Post created successfully!",
                "preview_url": file_url,
                "preview_type": preview_type,

                # Clear form after success
                "title": "",
                "description": "",
                "post_type": "",
                "subject": ""
            })

        except Exception as e:
            return render(request, "create-post-image-video.html", {
                "error": f"Error creating post: {str(e)}",
                "title": title,
                "description": description,
                "post_type": post_type,
                "subject": subject,
            })

    # GET
    return render(request, "create-post-image-video.html", {
        "profile_picture_url": profile_picture_url
    })

# --------------------------
# Create Post - Link
# --------------------------
def create_post_link(request):
    if "user_email" not in request.session:
        return redirect("/login/")

    # Get logged-in user
    user_email = request.session.get("user_email")
    user_resp = supabase.table("users").select("id, profile_picture").eq("email", user_email).maybe_single().execute()
    if not user_resp.data:
        return render(request, "create-post-text.html", {"error": "User not found."})
    user_data = user_resp.data
    user_id = user_data["id"]
    profile_picture_url = user_data.get("profile_picture")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        post_type = request.POST.get("post_type", "").strip()
        subject = request.POST.get("subject", "").strip()
        url = request.POST.get("url", "").strip()

        # Required fields check
        if not title or not post_type or not subject or not url:
            return render(
                request,
                "create-post-link.html",
                {
                    "error": "All fields are required.",
                    "title": title,
                    "post_type": post_type,
                    "subject": subject,
                    "url": url
                }
            )

        try:
            # Insert post
            supabase.table("posts").insert(
                {
                    "title": title,
                    "content": url,  # For link posts, URL = content
                    "post_type": post_type,
                    "subject": subject,
                    "user_id": user_id
                }
            ).execute()
            
            return render(
                request,
                "create-post-link.html",
                {"success": "Link post created successfully!",
                 "profile_picture_url": profile_picture_url}
            )

        except Exception as e:
            return render(
                request,
                "create-post-link.html",
                {
                    "error": f"Error creating post: {str(e)}",
                    "title": title,
                    "post_type": post_type,
                    "subject": subject,
                    "url": url,
                    "profile_picture_url": profile_picture_url
                }
            )

    # GET request
    return render(request, "create-post-link.html", {"profile_picture_url": profile_picture_url})

# --------------------------
# Profile Page
# --------------------------
def profile_page(request):
    # Require login
    if "user_email" not in request.session:
        return redirect("login")

    user_email = request.session.get("user_email")
    success = None

    # --------------------------
    # GET: Fetch current user
    # --------------------------
    response = supabase.table("users").select("*").eq("email", user_email).execute()
    if not response.data:
        return render(request, "profile_page.html", {"error": "User not found."})
    
    user = response.data[0]

    # Fix dates (remove timezone)
    if user.get("date_joined"):
        user["date_joined"] = datetime.fromisoformat(user["date_joined"][:10])
    if user.get("last_login"):
        user["last_login"] = datetime.fromisoformat(user["last_login"][:10])

    # --------------------------
    # POST: Update Profile
    # --------------------------
    if request.method == "POST":
        new_username = request.POST.get("username")
        new_bio = request.POST.get("bio")
        uploaded_file = request.FILES.get("profile_picture")
        remove_picture_flag = request.POST.get("remove_profile_picture") == "1"

        update_data = {
            "username": new_username,
            "bio": new_bio,
        }

        def storage_path_from_public_url(public_url, bucket_name):
            """Extract storage relative path from Supabase public URL.
            Expected format: .../storage/v1/object/public/<bucket>/<path>?...
            Returns '<path>' or None if not parsable.
            """
            try:
                base = public_url.split("?")[0]
                key = "/storage/v1/object/public/"
                if key in base:
                    after = base.split(key, 1)[1]  # '<bucket>/<path>'
                    bucket_in_url, rel_path = after.split("/", 1)
                    if bucket_in_url == bucket_name:
                        return rel_path
            except Exception:
                pass
            return None

        old_file_url = user.get("profile_picture")
        old_file_path = None
        if old_file_url:
            old_file_path = storage_path_from_public_url(old_file_url, settings.SUPABASE_BUCKET_PROFILE)

        # --------------------------
        # Remove existing picture
        # --------------------------
        if remove_picture_flag and old_file_url:
            try:
                bucket = settings.SUPABASE_BUCKET_PROFILE
                to_remove = []
                if old_file_path:
                    to_remove.append(old_file_path)

                # Also remove any other files left in the user's folder to ensure cleanup
                user_folder = f"profile_pictures/{user_email}"
                try:
                    # First attempt: direct list of the folder
                    listed = supabase.storage.from_(bucket).list(user_folder)
                    # supabase-py may return list or dict with 'data'
                    items = listed.get("data", listed) if isinstance(listed, dict) else listed
                    # No-op; ensure block is not empty
                    pass
                    # Fallback attempt: list from root with prefix (handles cases where 'user_folder' isn't treated as a directory)
                    if not items:
                        fallback = supabase.storage.from_(bucket).list("", {"prefix": user_folder})
                        items = fallback.get("data", fallback) if isinstance(fallback, dict) else fallback
                        # No-op; ensure block is not empty
                        pass
                    if items:
                        for item in items:
                            name = item.get("name") if isinstance(item, dict) else None
                            if name:
                                to_remove.append(f"{user_folder}/{name}")
                except Exception:
                    # listing failed; continue
                    pass

                # De-duplicate and remove
                if to_remove:
                    unique_paths = list(dict.fromkeys(to_remove))
                    # Ensure subsequent block has content
                    pass
                    supabase.storage.from_(bucket).remove(unique_paths)
                else:
                    # nothing to remove
                    pass

                # Verify removal; if any files still present, try prefix-based removal comprehensively
                try:
                    remaining = supabase.storage.from_(bucket).list(user_folder)
                    remaining_items = remaining.get("data", remaining) if isinstance(remaining, dict) else remaining
                    if not remaining_items:
                        remaining_prefix = supabase.storage.from_(bucket).list("", {"prefix": user_folder})
                        remaining_items = remaining_prefix.get("data", remaining_prefix) if isinstance(remaining_prefix, dict) else remaining_prefix
                    # Removed PFP-DELETE debug logs
                    if remaining_items:
                        # Attempt overwrite with zero bytes (break potential cache/stale state), then remove again
                        try:
                            for itm in remaining_items:
                                nm = itm.get("name") if isinstance(itm, dict) else None
                                if nm:
                                    pth = f"{user_folder}/{nm}"
                                    # Removed PFP-DELETE debug logs
                                    supabase.storage.from_(bucket).upload(pth, b"", file_options={"contentType": "application/octet-stream", "upsert": "true"})
                        except Exception as e:
                            # overwrite failed; continue
                            pass
                        # Build full paths from names and attempt second removal
                        retry_paths = []
                        for item in remaining_items:
                            nm = item.get("name") if isinstance(item, dict) else None
                            if nm:
                                retry_paths.append(f"{user_folder}/{nm}")
                        if retry_paths:
                            # Removed PFP-DELETE debug logs
                            supabase.storage.from_(bucket).remove(retry_paths)
                except Exception:
                    # verification failed; continue
                    pass
            except Exception:
                # swallow errors so UX isn't blocked, but attribute will be cleared
                pass
            update_data["profile_picture"] = None
            old_file_url = None  # prevent duplicate deletion below

        # --------------------------
        # Upload new picture
        # --------------------------
        if uploaded_file:
            import os
            # Ensure only one picture per user by clearing existing files in user's folder
            user_folder = f"profile_pictures/{user_email}"
            try:
                existing = supabase.storage.from_(settings.SUPABASE_BUCKET_PROFILE).list(user_folder)
                if existing:
                    # Build full relative paths to remove
                    to_remove = [f"{user_folder}/{item['name']}" for item in existing if 'name' in item]
                    if to_remove:
                        try:
                            supabase.storage.from_(settings.SUPABASE_BUCKET_PROFILE).remove(to_remove)
                        except Exception:
                            pass
            except Exception:
                # listing may fail; continue with upload
                pass

            # Use deterministic filename to avoid accumulating files
            _, ext = os.path.splitext(uploaded_file.name)
            # default to .jpg if no extension
            ext = ext if ext else ".jpg"
            file_path = f"{user_folder}/profile{ext}"
            file_bytes = uploaded_file.read()

            # Upload to Supabase Storage
            # Some clients support upsert; python client may overwrite when same path is used.
            supabase.storage.from_(settings.SUPABASE_BUCKET_PROFILE).upload(file_path, file_bytes)

            # Get public URL
            file_url = (
                supabase.storage
                .from_(settings.SUPABASE_BUCKET_PROFILE)
                .get_public_url(file_path)
                .split("?")[0]
            )
            update_data["profile_picture"] = file_url

        # --------------------------
        # Update user record
        # --------------------------
        supabase.table("users").update(update_data).eq("email", user_email).execute()
        success = "Profile updated successfully!"
        
        # Refresh user data in-place to reflect changes on profile page
        response = supabase.table("users").select("*").eq("email", user_email).execute()
        if response.data:
            user = response.data[0]
            if user.get("date_joined"):
                user["date_joined"] = datetime.fromisoformat(user["date_joined"][:10])
            if user.get("last_login"):
                user["last_login"] = datetime.fromisoformat(user["last_login"][:10])

    # --------------------------
    # Fetch user posts
    # --------------------------
    posts_resp = supabase.table("posts").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute()
    user_posts = posts_resp.data or []

    # Build formatted posts similar to home (without comments)
    formatted_posts = []
    for post in (user_posts or []):
        title = post.get("title") or "(No Title)"
        url = (post.get("content") or "").rstrip("?")
        course_name = post.get("subject") or "General"
        description = post.get("description", "")
        post_id = post.get("post_id")

        is_image = url.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"))
        is_video = url.lower().endswith((".mp4", ".webm", ".ogg"))

        # Votes for this post
        votes_resp = supabase.table("post_votes").select("*").eq("post_id", post_id).execute()
        votes = votes_resp.data or []
        upvotes = len([v for v in votes if v.get("vote_type") == "up"])
        downvotes = len([v for v in votes if v.get("vote_type") == "down"])
        net_votes = upvotes - downvotes

        # Current user's vote
        user_id = user.get("id")
        user_vote = None
        if user_id:
            uv = next((v["vote_type"] for v in votes if v.get("user_id") == user_id), None)
            if uv == "up":
                user_vote = "upvote"
            elif uv == "down":
                user_vote = "downvote"

        formatted_posts.append({
            "id": post_id,
            "title": title,
            "url": url,
            "description": description,
            "created_at": time_since(post.get("created_at")),
            "author": post.get("author", "Unknown"),
            "course": course_name,
            "is_image": is_image,
            "is_video": is_video,
            "upvote_count": upvotes,
            "downvote_count": downvotes,
            "vote_count": net_votes,
            "user_vote": user_vote,
            # comments intentionally omitted on profile page
        })

    # --------------------------
    # Fetch user's comments (flat list across posts)
    # --------------------------
    comments_resp = supabase.table("comments") \
        .select("*") \
        .eq("user_id", user["id"]) \
        .order("created_at", desc=True) \
        .execute()
    raw_comments = comments_resp.data or []

    user_comments = []
    seen_comment_ids = set()
    seen_composite = set()
    for c in raw_comments:
        cid = c.get("comment_id")
        pid = c.get("post_id")
        txt = (c.get("text") or "").strip()
        # Truncate created_at to seconds for stable duplicate detection
        created = (c.get("created_at") or "")
        created_key = created[:19] if isinstance(created, str) else str(created)[:19]

        if not cid:
            continue

        comp_key = (pid, txt, created_key)
        if cid in seen_comment_ids or comp_key in seen_composite:
            continue

        seen_comment_ids.add(cid)
        seen_composite.add(comp_key)

        # votes for comment (support both 'up'/'down' and 'upvote'/'downvote')
        cv_resp = supabase.table("comment_votes").select("vote_type").eq("comment_id", cid).execute()
        cvotes = cv_resp.data or []
        def as_dir(val):
            if not val:
                return None
            v = str(val).lower()
            if v in ("up", "upvote"): return "up"
            if v in ("down", "downvote"): return "down"
            return None
        up = sum(1 for v in cvotes if as_dir(v.get("vote_type")) == "up")
        down = sum(1 for v in cvotes if as_dir(v.get("vote_type")) == "down")
        net = up - down

        # post context (title)
        post_title = None
        try:
            p_resp = supabase.table("posts").select("title").eq("post_id", c["post_id"]).maybe_single().execute()
            if p_resp.data:
                post_title = p_resp.data.get("title") or "(No Title)"
        except Exception:
            post_title = "(No Title)"

        user_comments.append({
            "comment_id": cid,
            "post_id": pid,
            "post_title": post_title,
            "text": txt,
            "created_at": time_since(created),
            "net_votes": net,
            "edited": c.get("edited", False)
        })

    # ensure navbar gets the profile picture URL
    profile_picture_url = user.get("profile_picture") or None

    return render(request, "profile_page.html", {
        "user": user,
        "success": success,
        "user_posts": formatted_posts,  # use formatted posts
        "user_comments": user_comments, # NEW: flat comments list
        "profile_picture_url": profile_picture_url,
        "current_user_id": user.get("id")
    })

# ============================
# 🔵 HOME PAGE
# ============================
@login_required
def home(request):
    posts = Post.objects.all().order_by('-created_at')  # newest first
    context = {
        "posts": posts,
        "user_id": request.user.id,  # pass logged-in user's ID
    }
    return render(request, "home.html", context)

# ============================
# 🔵 EDIT POST
# ============================
def edit_post(request, post_id):

    # 1. Get logged-in user
    user_email = request.session.get("user_email")
    if not user_email:
        return HttpResponseForbidden("You must be logged in.")

    user_resp = supabase.table("users").select("id").eq("email", user_email).maybe_single().execute()
    user_id = user_resp.data["id"]

    # 2. Fetch post from Supabase
    post_resp = supabase.table("posts").select("*").eq("post_id", post_id).maybe_single().execute()
    post = post_resp.data

    if not post:
        return HttpResponseForbidden("Post not found.")

    # 3. Check ownership
    if post["user_id"] != user_id:
        return HttpResponseForbidden("You are not allowed to edit this post.")

    # 4. Infer content kind (Text / Media / Link) from stored content URL
    content = (post.get("content") or "").strip()
    lower_content = content.lower()

    media_exts = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".mp4", ".webm", ".ogg")
    if not content:
        post_kind = "Text"
    elif lower_content.endswith(media_exts):
        post_kind = "Media"
    else:
        post_kind = "Link"

    # ==========================
    # GET → Return form HTML snippet
    # ==========================
    if request.method == "GET":
        html = render_to_string("edit_post_form.html", {"post": post, "subjects": SUBJECTS, "post_kind": post_kind})
        return HttpResponse(html)

    # ==========================
    # POST → Save changes to Supabase
    # ==========================
    # Always allow updating the title
    new_title = (request.POST.get("title") or "").strip()

    update_data = {
        "title": new_title,
        "updated_at": "now()",
    }

    # Common subject handling (all post types have a subject)
    new_subject = (request.POST.get("subject") or post.get("subject") or "").strip()
    if new_subject:
        update_data["subject"] = new_subject

    # Tag handling: post_type column stores tag (question/announcement/discussion)
    new_tag = (request.POST.get("post_type") or post.get("post_type") or "").strip()
    if new_tag:
        update_data["post_type"] = new_tag

    # Text posts → title, subject, body/description (1000 chars max)
    if post_kind == "Text":
        new_description = (request.POST.get("description") or "").strip()
        if len(new_description) > 1000:
            new_description = new_description[:1000]
        update_data["description"] = new_description

    # Media posts → title, subject, optional description (1000 chars max), optional media replacement
    elif post_kind == "Media":
        new_description = (request.POST.get("description") or "").strip()
        if len(new_description) > 1000:
            new_description = new_description[:1000]
        update_data["description"] = new_description

        # If a new file is uploaded, replace the existing media
        uploaded_file = request.FILES.get("fileUpload")
        if uploaded_file:
            try:
                file_path = f"{user_email}/{uploaded_file.name}"
                file_bytes = uploaded_file.read()

                supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                    file_path,
                    file_bytes
                )

                file_url = supabase.storage.from_(settings.SUPABASE_BUCKET) \
                    .get_public_url(file_path) \
                    .split("?")[0]

                update_data["content"] = file_url
            except Exception:
                # Fail gracefully: keep existing media if upload fails
                pass

    # Link posts → title, subject, URL stored in content
    elif post_kind == "Link":
        new_url = (request.POST.get("url") or post.get("content") or "").strip()
        update_data["content"] = new_url

    # Perform update without changing inferred content kind
    supabase.table("posts").update(update_data).eq("post_id", post_id).execute()

    return redirect(request.META.get("HTTP_REFERER", "/"))


# ============================
# 🔴 DELETE POST
# ============================
def delete_post(request, post_id):
    if request.method != "POST":
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # Check session user
    user_email = request.session.get("user_email")
    if not user_email:
        return HttpResponseForbidden("You must be logged in.")

    # Get logged-in user ID
    user_resp = supabase.table("users").select("id").eq("email", user_email).maybe_single().execute()
    user_id = user_resp.data["id"] if user_resp.data else None

    # Fetch post (IMPORTANT: use post_id column)
    post_resp = supabase.table("posts").select("*").eq("post_id", post_id).maybe_single().execute()
    post = post_resp.data
    if not post:
        return HttpResponseForbidden("Post not found.")

    # Check ownership
    if post["user_id"] != user_id:
        return HttpResponseForbidden("You are not allowed to delete this post.")

    # If post has media content in Storage, delete the file from the post_media bucket
    content_url = (post.get("content") or "").strip()
    if content_url:
        try:
            # Extract storage path: after '/storage/v1/object/public/<bucket>/'
            base = content_url.split("?")[0]
            key = "/storage/v1/object/public/"
            if key in base:
                prefix_idx = base.find(key)
                remainder = base[prefix_idx + len(key):]  # '<bucket>/<path>'
                parts = remainder.split("/", 1)
                bucket_name = parts[0] if parts else settings.SUPABASE_BUCKET
                rel_path = parts[1] if len(parts) > 1 else ""
                if rel_path:
                    supabase.storage.from_(bucket_name).remove([rel_path])
        except Exception:
            # Swallow storage errors so delete continues
            pass

    # Delete post (IMPORTANT: use post_id column)
    try:
        supabase.table("posts").delete().eq("post_id", post_id).execute()
    except Exception as e:
        if "Missing response" not in str(e):
            raise e

    return redirect(request.META.get('HTTP_REFERER', '/'))



# --------------------------
# Report Post
# --------------------------
@csrf_exempt
def report_post(request):
    """Handle post reporting functionality"""
    if "user_email" not in request.session:
        return JsonResponse({"error": "Login required"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    user_email = request.session.get("user_email")

    # Validate and normalize incoming form fields before DB operations
    post_id_raw = request.POST.get("post_id")
    violation_type = (request.POST.get("violation_type") or "").strip()
    details = (request.POST.get("details") or "").strip()

    if not post_id_raw:
        return JsonResponse({"error": "Missing post_id"}, status=400)

    try:
        post_id = int(post_id_raw)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid post ID"}, status=400)

    if not violation_type:
        return JsonResponse({"error": "Missing violation type"}, status=400)

    try:
        # Get user ID
        user_resp = supabase.table("users").select("id").eq("email", user_email).maybe_single().execute()
        if not user_resp or not getattr(user_resp, "data", None):
            return JsonResponse({"error": "User not found"}, status=404)
        user_id = user_resp.data["id"]

        # Check if post exists
        post_resp = supabase.table("posts").select("*").eq("post_id", post_id).maybe_single().execute()
        if not post_resp or not getattr(post_resp, "data", None):
            return JsonResponse({"error": "Post not found"}, status=404)

        # Check if user already reported this post
        existing_report_resp = supabase.table("post_reports") \
            .select("*") \
            .eq("post_id", post_id) \
            .eq("reporter_id", user_id) \
            .maybe_single() \
            .execute()

        existing_report = existing_report_resp.data if existing_report_resp and getattr(existing_report_resp, "data", None) else None
        if existing_report:
            return JsonResponse({"error": "You have already reported this post"}, status=409)

        # Store violation type together with user description in the existing 'reason' column
        # Example: "[spam] This is spam"
        details_tagged = f"[{violation_type}] {details}" if details else f"[{violation_type}]"

        # Create the report using only real columns from Supabase post_reports
        report_data = {
            "post_id": post_id,
            "reporter_id": user_id,
            "reason": details_tagged,
            "created_at": datetime.now(timezone.utc).isoformat(),  # optional; Supabase also has a default
        }

        report_resp = supabase.table("post_reports").insert(report_data).execute()
        
        if report_resp and getattr(report_resp, "data", None):
            return JsonResponse({
                "success": True,
                "message": "Report submitted successfully. Thank you for helping keep our community safe."
            })
        else:
            return JsonResponse({"error": "Failed to submit report"}, status=500)

    except Exception as e:
        print(f"Error submitting report: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": "An error occurred while submitting the report"}, status=500)


from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timezone

# --------------------------
# Admin Page
# --------------------------
def admin_page(request):
    """Admin dashboard page"""
    # Check if user is logged in and is admin
    if "user_email" not in request.session:
        return redirect("login")
    
    user_email = request.session.get("user_email")
    if user_email != "admin@gmail.com":
        return redirect("home")  # Redirect non-admin users
    
    try:
        # Get total users count
        print("Fetching users from Supabase...")
        users_resp = supabase.table("users").select("*").execute()
        print(f"Users response: {users_resp}")
        users = users_resp.data if users_resp.data else []
        total_users = len(users)
        print(f"Total users found: {total_users}")
        
        # Get posts by subject
        print("Fetching posts from Supabase...")
        posts_resp = supabase.table("posts").select("*").execute()
        print(f"Posts response: {posts_resp}")
        posts = posts_resp.data if posts_resp.data else []
        print(f"Total posts found: {len(posts)}")
        
        # Count posts by subject
        posts_by_subject = {}
        for post in posts:
            subject = post.get("course", post.get("subject", "Unknown"))
            if subject not in posts_by_subject:
                posts_by_subject[subject] = []
            posts_by_subject[subject].append(post)
        
        # Get reports with user and post details
        print("Fetching reports from Supabase...")
        reports_resp = supabase.table("post_reports") \
            .select("*") \
            .order("created_at", desc=True) \
            .execute()
        print(f"Reports response: {reports_resp}")
        reports = reports_resp.data if reports_resp.data else []
        print(f"Total reports found: {len(reports)}")

        violation_labels = {
            "inappropriate_content": "Inappropriate Content",
            "harassment": "Harassment",
            "spam": "Spam",
            "plagiarism": "Plagiarism",
            "misinformation": "Misinformation",
            "hate_speech": "Hate Speech",
            "violence": "Violence or Threats",
            "copyright": "Copyright Violation",
            "other": "Other",
        }
        
        # Enhance reports with user, post, and parsed reason/details
        enhanced_reports = []
        for report in reports:
            print(f"Processing report: {report}")
            
            # Get post details - try different column names
            post_id = report.get("post_id")
            if not post_id:
                print("No post_id found in report")
                continue
                
            post_resp = supabase.table("posts") \
                .select("*") \
                .eq("post_id", post_id) \
                .maybe_single() \
                .execute()
            
            # Get reporter details
            reporter_id = report.get("reporter_id")
            reporter_resp = None
            if reporter_id:
                reporter_resp = supabase.table("users") \
                    .select("username, email") \
                    .eq("id", reporter_id) \
                    .maybe_single() \
                    .execute()
            
            # Get post author details
            post_author_resp = None
            if post_resp and post_resp.data:
                author_id = post_resp.data.get("user_id")
                if author_id:
                    post_author_resp = supabase.table("users") \
                        .select("username, email") \
                        .eq("id", author_id) \
                        .maybe_single() \
                        .execute()

            # Derive basic media info for the reported post (image/video/link)
            post_url = ""
            post_is_image = False
            post_is_video = False
            if post_resp and post_resp.data:
                post_url = (post_resp.data.get("content") or "").rstrip("?")
                url_lower = post_url.lower()
                post_is_image = url_lower.endswith((".jpg", ".jpeg", ".png", ".gif"))
                post_is_video = url_lower.endswith((".mp4", ".webm", ".ogg"))

            # Our Supabase schema uses 'reason' to store the violation code and user description
            raw_details = (report.get("reason") or "").strip()
            violation_code = None
            violation_label = "Unknown"
            user_description = ""

            if raw_details.startswith("[") and "]" in raw_details:
                end_idx = raw_details.find("]")
                violation_code = raw_details[1:end_idx]
                violation_label = violation_labels.get(
                    violation_code,
                    violation_code.replace("_", " ").title() if violation_code else "Unknown",
                )
                user_description = raw_details[end_idx + 1 :].strip()
            else:
                user_description = raw_details
            
            # Use the real status column if present; default to 'pending'
            status_val = report.get("status") or "pending"

            enhanced_report = {
                **report,
                "post_title": post_resp.data.get("title", "Untitled Post") if post_resp and post_resp.data else "Post not found",
                "post_subject": post_resp.data.get("course", post_resp.data.get("subject", "Unknown")) if post_resp and post_resp.data else "Unknown",
                "post_description": post_resp.data.get("description", "") if post_resp and post_resp.data else "",
                # Prefer author email for clarity in moderation view
                "post_author": post_author_resp.data.get("email", "Unknown") if post_author_resp and post_author_resp.data else "Unknown",
                # Reporter info: always expose email; username falls back to email if missing
                "reporter_email": reporter_resp.data.get("email", "Unknown") if reporter_resp and reporter_resp.data else "Unknown",
                "reporter_username": (
                    reporter_resp.data.get("username")
                    if reporter_resp and reporter_resp.data and reporter_resp.data.get("username")
                    else (reporter_resp.data.get("email") if reporter_resp and reporter_resp.data else "Unknown")
                ),
                "violation_code": violation_code,
                "violation_label": violation_label,
                "user_description": user_description,
                "post_url": post_url,
                "post_is_image": post_is_image,
                "post_is_video": post_is_video,
                "status": status_val,
            }
            enhanced_reports.append(enhanced_report)
            print(f"Enhanced report: {enhanced_report}")

        # -----------------------------------
        # Get comment reports with details
        # -----------------------------------
        print("Fetching comment reports from Supabase...")
        comment_reports_resp = supabase.table("comment_reports") \
            .select("*") \
            .order("created_at", desc=True) \
            .execute()
        print(f"Comment reports response: {comment_reports_resp}")
        comment_reports_raw = comment_reports_resp.data if comment_reports_resp and getattr(comment_reports_resp, "data", None) else []
        print(f"Total comment reports found: {len(comment_reports_raw)}")

        enhanced_comment_reports = []
        for c_report in comment_reports_raw:
            print(f"Processing comment report: {c_report}")

            comment_id = c_report.get("comment_id")
            if not comment_id:
                print("No comment_id found in comment_report")
                continue

            # Get the reported comment
            comment_resp = supabase.table("comments") \
                .select("*") \
                .eq("comment_id", comment_id) \
                .maybe_single() \
                .execute()

            if not comment_resp or not getattr(comment_resp, "data", None):
                print(f"Comment not found for comment_id={comment_id}")
                continue

            comment_data = comment_resp.data
            comment_text = comment_data.get("text", "")
            post_id = comment_data.get("post_id")
            comment_author_id = comment_data.get("user_id")

            # Get the parent post for subject/title/description
            post_title = "Post not found"
            post_subject = "Unknown"
            post_description = ""
            post_resp = None
            if post_id:
                post_resp = supabase.table("posts") \
                    .select("*") \
                    .eq("post_id", post_id) \
                    .maybe_single() \
                    .execute()

            if post_resp and getattr(post_resp, "data", None):
                post_title = post_resp.data.get("title", "Untitled Post")
                post_subject = post_resp.data.get("course", post_resp.data.get("subject", "Unknown"))
                post_description = post_resp.data.get("description", "")

            # Comment author details
            comment_author_email = "Unknown"
            if comment_author_id:
                comment_author_resp = supabase.table("users") \
                    .select("username, email") \
                    .eq("id", comment_author_id) \
                    .maybe_single() \
                    .execute()
                if comment_author_resp and getattr(comment_author_resp, "data", None):
                    comment_author_email = (
                        comment_author_resp.data.get("email")
                        or comment_author_resp.data.get("username")
                        or "Unknown"
                    )

            # Reporter details
            reporter_id = c_report.get("reporter_id")
            reporter_email = "Unknown"
            reporter_username = "Unknown"
            if reporter_id:
                reporter_resp = supabase.table("users") \
                    .select("username, email") \
                    .eq("id", reporter_id) \
                    .maybe_single() \
                    .execute()
                if reporter_resp and getattr(reporter_resp, "data", None):
                    reporter_email = reporter_resp.data.get("email", "Unknown")
                    reporter_username = (
                        reporter_resp.data.get("username")
                        or reporter_resp.data.get("email")
                        or "Unknown"
                    )

            # Violation info from reason/description columns
            violation_code = (c_report.get("reason") or "").strip() or "other"
            violation_label = violation_labels.get(
                violation_code,
                violation_code.replace("_", " ").title() if violation_code else "Unknown",
            )
            user_description = (c_report.get("description") or "").strip()

            status_val = c_report.get("status") or "pending"

            enhanced_comment = {
                **c_report,
                "post_title": post_title,
                "post_subject": post_subject,
                "post_description": post_description,
                "comment_text": comment_text,
                "comment_author": comment_author_email,
                "reporter_email": reporter_email,
                "reporter_username": reporter_username,
                "violation_code": violation_code,
                "violation_label": violation_label,
                "user_description": user_description,
                "status": status_val,
            }
            enhanced_comment_reports.append(enhanced_comment)
            print(f"Enhanced comment report: {enhanced_comment}")

        context = {
            "total_users": total_users,
            "users": users,
            "posts_by_subject": posts_by_subject,
            "total_posts": len(posts),
            "reports": enhanced_reports,
            "total_reports": len(enhanced_reports),
            "comment_reports": enhanced_comment_reports,
            "total_comment_reports": len(enhanced_comment_reports),
            "subjects": SUBJECTS,  # Make sure SUBJECTS is defined
            "active_subjects": len(SUBJECTS),
        }
        
        return render(request, "admin_dashboard.html", context)
        
    except Exception as e:
        print(f"Error loading admin page: {str(e)}")
        import traceback
        traceback.print_exc()
        return render(request, "admin_dashboard.html", {
            "total_users": 0,
            "users": [],
            "posts_by_subject": {},
            "total_posts": 0,
            "reports": [],
            "total_reports": 0,
            "subjects": SUBJECTS,
            "active_subjects": len(SUBJECTS),
            "error": f"Failed to load admin data: {str(e)}"
        })


# --------------------------
# Admin API Endpoints
# --------------------------
@csrf_exempt
def admin_subject_posts(request):
    """API endpoint to get posts by subject for admin"""
    if "user_email" not in request.session or request.session.get("user_email") != "admin@gmail.com":
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    subject = request.GET.get("subject", "")
    if not subject:
        return JsonResponse({"error": "Subject parameter required"}, status=400)
    
    try:
        # Get posts for the subject (text column 'subject')
        posts_resp = supabase.table("posts") \
            .select("*") \
            .eq("subject", subject) \
            .order("created_at", desc=True) \
            .execute()

        raw_posts = posts_resp.data if posts_resp.data else []

        # Build full objects matching home.html needs
        full_posts = []
        for p in raw_posts:
            author_email = "unknown@example.com"
            if p.get("user_id") is not None:
                u = supabase.table("users").select("email").eq("id", p["user_id"]).maybe_single().execute()
                if u and u.data and "email" in u.data:
                    author_email = u.data["email"]

            url = (p.get("content") or "").rstrip("?")
            is_image = url.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
            is_video = url.lower().endswith((".mp4", ".webm", ".ogg"))

            full_posts.append({
                "id": p.get("post_id"),
                "title": p.get("title") or "(No Title)",
                "description": p.get("description") or "",
                "url": url,
                "created_at": p.get("created_at"),
                "subject": p.get("subject") or p.get("course") or "Unknown",
                "user_id": p.get("user_id"),
                "author": author_email,
                "is_image": is_image,
                "is_video": is_video,
            })

        return JsonResponse({"posts": full_posts})
        
    except Exception as e:
        print(f"Error fetching subject posts: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": f"Failed to fetch posts: {str(e)}"}, status=500)

@csrf_exempt
def admin_update_report(request):
    """API endpoint to update report status"""
    if "user_email" not in request.session or request.session.get("user_email") != "admin@gmail.com":
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
    try:
        report_id = request.POST.get("report_id")
        new_status = request.POST.get("status")
        
        if not report_id or not new_status:
            return JsonResponse({"error": "Missing required fields"}, status=400)
        
        # Convert report_id to int
        try:
            report_id = int(report_id)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid report ID format"}, status=400)
        
        # Validate status
        valid_statuses = ["pending", "under_review", "resolved", "dismissed"]
        if new_status not in valid_statuses:
            return JsonResponse({"error": "Invalid status value"}, status=400)
        
        # Update report status
        update_resp = supabase.table("post_reports") \
            .update({
                "status": new_status,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }) \
            .eq("report_id", report_id) \
            .execute()
        
        if update_resp.data:
            return JsonResponse({"success": True, "message": "Report updated successfully"})
        else:
            return JsonResponse({"error": "Failed to update report - no data returned"}, status=500)
            
    except Exception as e:
        print(f"Error updating report: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": f"Failed to update report: {str(e)}"}, status=500)


@csrf_exempt
def admin_update_comment_report(request):
    """API endpoint to update comment report status"""
    if "user_email" not in request.session or request.session.get("user_email") != "admin@gmail.com":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        report_id = request.POST.get("report_id")
        new_status = request.POST.get("status")

        if not report_id or not new_status:
            return JsonResponse({"error": "Missing required fields"}, status=400)

        try:
            report_id = int(report_id)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid report ID format"}, status=400)

        valid_statuses = ["pending", "under_review", "resolved", "dismissed"]
        if new_status not in valid_statuses:
            return JsonResponse({"error": "Invalid status value"}, status=400)

        update_resp = supabase.table("comment_reports") \
            .update({
                "status": new_status,
                "reviewed_at": datetime.now(timezone.utc).isoformat()
            }) \
            .eq("report_id", report_id) \
            .execute()

        if update_resp.data:
            return JsonResponse({"success": True, "message": "Comment report updated successfully"})
        else:
            return JsonResponse({"error": "Failed to update comment report - no data returned"}, status=500)

    except Exception as e:
        print(f"Error updating comment report: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": f"Failed to update comment report: {str(e)}"}, status=500)


# --------------------------
# Admin: All Posts API (for dashboard Recent Activity full list)
# --------------------------
@csrf_exempt
def admin_all_posts(request):
    if "user_email" not in request.session or request.session.get("user_email") != "admin@gmail.com":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        posts_resp = supabase.table("posts").select("*").order("created_at", desc=True).execute()
        raw_posts = posts_resp.data if posts_resp.data else []

        full_posts = []
        for p in raw_posts:
            author_email = "unknown@example.com"
            if p.get("user_id") is not None:
                u = supabase.table("users").select("email").eq("id", p["user_id"]).maybe_single().execute()
                if u and u.data and "email" in u.data:
                    author_email = u.data["email"]

            url = (p.get("content") or "").rstrip("?")
            is_image = url.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
            is_video = url.lower().endswith((".mp4", ".webm", ".ogg"))

            full_posts.append({
                "id": p.get("post_id"),
                "title": p.get("title") or "(No Title)",
                "description": p.get("description") or "",
                "url": url,
                "created_at": p.get("created_at"),
                "subject": p.get("subject") or p.get("course") or "Unknown",
                "user_id": p.get("user_id"),
                "author": author_email,
                "is_image": is_image,
                "is_video": is_video,
            })

        return JsonResponse({"posts": full_posts})
    except Exception as e:
        return JsonResponse({"error": f"Failed to fetch posts: {str(e)}"}, status=500)


# --------------------------
# Admin-only delete post
# --------------------------
@csrf_exempt
def admin_delete_post(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    if "user_email" not in request.session or request.session.get("user_email") != "admin@gmail.com":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        post_id = int(request.POST.get("post_id"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid post ID"}, status=400)

    try:
        supabase.table("posts").delete().eq("post_id", post_id).execute()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# --------------------------
# Admin-only delete comment (from Reports)
# --------------------------
@csrf_exempt
def admin_delete_comment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    if "user_email" not in request.session or request.session.get("user_email") != "admin@gmail.com":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        comment_id = int(request.POST.get("comment_id"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid comment ID"}, status=400)

    try:
        supabase.table("comments").delete().eq("comment_id", comment_id).execute()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# --------------------------
# Logout
# --------------------------
def logout_page(request):
    request.session.flush()
    return redirect("/")


# --------------------------
# Diagnostics: env + static
# --------------------------
def diagnostics(request):
    info = {
        "RENDER": os.environ.get("RENDER"),
        "DEBUG": settings.DEBUG,
        "ALLOWED_HOSTS": settings.ALLOWED_HOSTS,
        "STATIC_URL": settings.STATIC_URL,
        "STATIC_ROOT": str(getattr(settings, "STATIC_ROOT", "")),
        "STATICFILES_DIRS": [str(p) for p in getattr(settings, "STATICFILES_DIRS", [])],
        "WHITENOISE_ENABLED": "whitenoise.middleware.WhiteNoiseMiddleware" in settings.MIDDLEWARE,
    }

    # Add static assets diagnostics using direct path checks (robust even with Manifest storage)
    try:
        assets = [
            "css/post.css",
            "js/comments.js",
            "js/post_menu.js",
            "js/media_modal.js",
        ]
        resolved = {}
        static_dirs = getattr(settings, "STATICFILES_DIRS", [])
        for rel in assets:
            found_path = None
            size = None
            for d in static_dirs:
                candidate = os.path.join(d, rel)
                if os.path.exists(candidate):
                    found_path = candidate
                    try:
                        size = os.path.getsize(candidate)
                    except Exception:
                        size = None
                    break
            resolved[rel] = {
                "found": bool(found_path),
                "path": found_path,
                "size": size,
            }
        info["assets"] = resolved
    except Exception as e:
        info["assets_error"] = str(e)

    return JsonResponse(info)
