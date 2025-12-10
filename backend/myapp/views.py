from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime, timezone, timedelta
from supabase import create_client
from django.http import HttpResponseForbidden
import time
import secrets


# --------------------------
# Initialize Supabase client (use service role if available)
# --------------------------
SUPABASE_AUTH_KEY = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None) or settings.SUPABASE_KEY
supabase = create_client(settings.SUPABASE_URL, SUPABASE_AUTH_KEY)

# --------------------------
# Utility: Safe Supabase execute with retries
# --------------------------
def safe_execute(request_fn, retries=3, delay=0.1):
    """
    request_fn: lambda that calls supabase execute()
    retries: number of retries on failure
    delay: seconds to wait between retries
    """
    for attempt in range(retries):
        try:
            return request_fn()
        except Exception as e:
            if "non-blocking socket" in str(e) or "RemoteProtocolError" in str(e):
                time.sleep(delay)
                continue
            raise
    # final attempt
    return request_fn()

# --------------------------
# Redirect root to login
# --------------------------
def root_redirect(request):
    return redirect("/login/")

# --------------------------
# Helper: Fetch profile picture URL for navbar
# --------------------------
def get_profile_picture_url(request):
    email = request.session.get("user_email")
    if not email:
        return None
    resp = supabase.table("users").select("profile_picture").eq("email", email).maybe_single().execute()
    return resp.data.get("profile_picture") if resp and resp.data else None

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
        role = request.POST.get("role", "").strip().lower()

        # ---------- Validation ----------
        if not email or not password or not confirm or not role:
            return render(request, "register.html", {"error": "All fields are required."})
        if password != confirm:
            return render(request, "register.html", {"error": "Passwords do not match."})
        if role not in ["student", "teacher"]:
            return render(request, "register.html", {"error": "Invalid role selected."})

        # ---------- Check if email exists ----------
        try:
            existing = supabase.table("users").select("*").eq("email", email).execute()
            if existing.data:
                return render(request, "register.html", {"error": "Account already exists. Please login."})
        except Exception as e:
            return render(request, "register.html", {"error": f"Database error: {str(e)}"})

        # ---------- Insert User ----------
        password_hash = make_password(password)
        date_joined = datetime.now(timezone.utc).isoformat()
        try:
            response = supabase.table("users").insert({
                "email": email,
                "password_hash": password_hash,
                "role": role,
                "username": username if username else None,
                "profile_picture": None,
                "bio": None,
                "last_login": None,
                "date_joined": date_joined
            }).execute()
            if getattr(response, "error", None):
                return render(request, "register.html", {"error": f"Error registering: {response.error}"})
        except Exception as e:
            return render(request, "register.html", {"error": f"Error registering: {str(e)}"})

        return redirect("/login/")

    # include navbar pfp (in case navbar is used on this page)
    return render(request, "register.html", {
        "profile_picture_url": get_profile_picture_url(request)
    })

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

        # Update last_login timestamp (non-blocking)
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
            # Get author email
            user_resp = supabase.table("users").select("email").eq("id", c["user_id"]).maybe_single().execute()
            author_email = user_resp.data["email"] if user_resp.data and "email" in user_resp.data else "anonymous@example.com"

            # Fetch votes
            votes_resp = supabase.table("comment_votes").select("*").eq("comment_id", c["comment_id"]).execute()
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

    user_email = request.session.get("user_email")
    # Wrap Supabase calls with retries to avoid transient disconnects
    user_resp = safe_execute(lambda: supabase.table("users").select("*").eq("email", user_email).maybe_single().execute())
    profile_picture_url = user_resp.data["profile_picture"] if user_resp.data and user_resp.data.get("profile_picture") else None

    # -----------------------------
    # Handle new comment or reply
    # -----------------------------
    if request.method == "POST":
        post_id = request.POST.get("post_id")
        comment_text = request.POST.get("comment")
        parent_id = request.POST.get("parent_id")

        # Get user_id
        user_resp = supabase.table("users").select("id").eq("email", user_email).maybe_single().execute()
        user_id = user_resp.data["id"] if user_resp.data else None

        if post_id and comment_text and user_id:
            supabase.table("comments").insert({
                "post_id": post_id,
                "user_id": user_id,
                "parent_id": parent_id,
                "text": comment_text,
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()

        return redirect("/home/")

    # -----------------------------
    # Fetch posts
    # -----------------------------
    response = safe_execute(lambda: supabase.table("posts").select("*").order("created_at", desc=True).execute())
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
        course_name = post.get("course_id") or "null"
        description = post.get("description", "")
        post_id = post.get("post_id")

        is_image = url.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
        is_video = url.lower().endswith((".mp4", ".webm", ".ogg"))

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
        # Fetch all comments for this post
        # -----------------------------
        comment_resp = safe_execute(lambda: supabase.table("comments").select("*").eq("post_id", post_id).order("created_at", desc=False).execute())
        all_comments = comment_resp.data if comment_resp.data else []

        # Deduplicate comments to avoid double-rendering
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

        # -----------------------------
        # Build nested comment tree
        # -----------------------------
        nested_comments = build_comment_tree(dedup_comments, user_id=user_id)

        formatted_posts.append({
            "id": post_id,
            "title": title,
            "url": url,
            "description": description,
            "created_at": time_since(post.get("created_at")),
            "author": post.get("author", "Unknown"),
            "course": f"c/{course_name}",
            "is_image": is_image,
            "is_video": is_video,
            "comments": nested_comments,
            "upvote_count": upvotes,
            "downvote_count": downvotes,
            "vote_count": net_votes,
            "user_vote": user_vote,
            "comment_count": len(dedup_comments)
        })

    # Pull and clear any success message (e.g., from profile edit)
    success_message = request.session.pop("success_message", None)

    return render(request, "home.html", {
        "user_email": user_email,
        "role": request.session.get("role", "student"),
        "posts": formatted_posts,
        "profile_picture_url": profile_picture_url,  # unchanged
        "success": success_message,
    })

# --------------------------
# Comment Editing & Deletion
# --------------------------
def edit_comment(request, comment_id):
    if request.method != "POST":
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # Fetch comment
    resp = supabase.table("comments").select("*").eq("comment_id", comment_id).maybe_single().execute()
    comment = resp.data
    if not comment:
        return HttpResponseForbidden("Comment not found.")

    # Get current user
    user_email = request.session.get("user_email")
    user_resp = supabase.table("users").select("id").eq("email", user_email).maybe_single().execute()
    user_id = user_resp.data["id"] if user_resp.data else None

    if comment["user_id"] != user_id:
        return HttpResponseForbidden("You can't edit this comment.")

    # Update comment
    supabase.table("comments").update({
        "text": request.POST.get("comment"),
        "edited": True
    }).eq("comment_id", comment_id).execute()

    return redirect(request.META.get('HTTP_REFERER', '/'))


def delete_comment(request, comment_id):
    if request.method != "POST":
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # Fetch comment
    resp = supabase.table("comments").select("*").eq("comment_id", comment_id).maybe_single().execute()
    comment = resp.data
    if not comment:
        return HttpResponseForbidden("Comment not found.")

    # Get current user
    user_email = request.session.get("user_email")
    user_resp = supabase.table("users").select("id").eq("email", user_email).maybe_single().execute()
    user_id = user_resp.data["id"] if user_resp.data else None

    if comment["user_id"] != user_id:
        return HttpResponseForbidden("You can't delete this comment.")

    # Delete comment
    supabase.table("comments").delete().eq("comment_id", comment_id).execute()
    return redirect(request.META.get('HTTP_REFERER', '/'))


# --------------------------
# Comment Voting
# --------------------------
@csrf_exempt
def vote_comment(request, comment_id, vote_type):
    if "user_email" not in request.session:
        return JsonResponse({"error": "Login required"}, status=403)

    user_email = request.session.get("user_email")

    # Fetch user ID safely
    user_resp = supabase.table("users").select("id").eq("email", user_email).maybe_single().execute()
    if not user_resp or not user_resp.data:
        return JsonResponse({"error": "User not found"}, status=404)

    user_id = user_resp.data["id"]

    # Check if vote exists for this user/comment
    existing_vote_resp = supabase.table("comment_votes") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("comment_id", comment_id) \
        .maybe_single() \
        .execute()

    existing_vote = existing_vote_resp.data if existing_vote_resp and existing_vote_resp.data else None

    # Process voting logic
    if existing_vote:
        if existing_vote["vote_type"] == vote_type:
            # Same vote again → remove it (unvote)
            supabase.table("comment_votes").delete().eq("vote_id", existing_vote["vote_id"]).execute()
            message = "Vote removed"
        else:
            # Switch vote type
            supabase.table("comment_votes").update({"vote_type": vote_type}).eq("vote_id", existing_vote["vote_id"]).execute()
            message = "Vote updated"
    else:
        # New vote
        supabase.table("comment_votes").insert({
            "user_id": user_id,
            "comment_id": comment_id,
            "vote_type": vote_type
        }).execute()
        message = "Vote added"

    # Get updated totals
    votes_resp = supabase.table("comment_votes") \
        .select("vote_type") \
        .eq("comment_id", comment_id) \
        .execute()

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
    user_resp = supabase.table("users").select("id").eq("email", user_email).maybe_single().execute()
    if not user_resp or not user_resp.data:
        return JsonResponse({"error": "User not found"}, status=404)

    user_id = user_resp.data["id"]

    # Check existing vote
    existing_vote_resp = supabase.table("post_votes") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("post_id", post_id) \
        .maybe_single() \
        .execute()

    existing_vote = existing_vote_resp.data if existing_vote_resp and existing_vote_resp.data else None

    # Process voting
    if existing_vote:
        if existing_vote["vote_type"] == vote_type:
            # Same vote → remove it
            supabase.table("post_votes").delete().eq("vote_id", existing_vote["vote_id"]).execute()
            message = "Vote removed"
        else:
            # Switch vote
            supabase.table("post_votes").update({"vote_type": vote_type}).eq("vote_id", existing_vote["vote_id"]).execute()
            message = "Vote updated"
    else:
        # New vote
        supabase.table("post_votes").insert({
            "user_id": user_id,
            "post_id": post_id,
            "vote_type": vote_type
        }).execute()
        message = "Vote added"

    # Compute net votes
    votes_resp = supabase.table("post_votes").select("vote_type").eq("post_id", post_id).execute()
    total_votes = sum(1 if v["vote_type"] == "up" else -1 for v in (votes_resp.data or []))

    return JsonResponse({
        "message": message,
        "net_votes": total_votes,       # Matches frontend key
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
    user_resp = supabase.table("users").select("id").eq("email", user_email).maybe_single().execute()
    if not user_resp.data:
        return JsonResponse({"error": "User not found"}, status=404)
    user_id = user_resp.data["id"]

    # Validate vote type
    if vote_type not in FRONTEND_TO_DB:
        return JsonResponse({"error": "Invalid vote type"}, status=400)
    db_vote_value = FRONTEND_TO_DB[vote_type]

    # Check if post exists
    post_resp = supabase.table("posts").select("post_id").eq("post_id", post_id).maybe_single().execute()
    if not post_resp.data:
        return JsonResponse({"error": "Post not found"}, status=404)

    # Check for existing vote
    existing_vote_resp = supabase.table("post_votes")\
        .select("*")\
        .eq("post_id", post_id)\
        .eq("user_id", user_id)\
        .maybe_single()\
        .execute()
    existing_vote = existing_vote_resp.data if existing_vote_resp and existing_vote_resp.data else None

    user_vote = None

    if existing_vote:
        if existing_vote.get("vote_type") == db_vote_value:
            # Same vote again → remove vote
            supabase.table("post_votes").delete().eq("vote_id", existing_vote["vote_id"]).execute()
        else:
            # Change vote type
            supabase.table("post_votes").update({"vote_type": db_vote_value}).eq("vote_id", existing_vote["vote_id"]).execute()
            user_vote = vote_type
    else:
        # Insert new vote safely
        try:
            supabase.table("post_votes").insert({
                "user_id": user_id,
                "post_id": post_id,
                "vote_type": db_vote_value
            }).execute()
            user_vote = vote_type
        except Exception as e:
            if "duplicate key value" in str(e):
                # Handle race condition / duplicate insert
                existing_vote_resp = supabase.table("post_votes")\
                    .select("*")\
                    .eq("post_id", post_id)\
                    .eq("user_id", user_id)\
                    .maybe_single()\
                    .execute()
                existing_vote = existing_vote_resp.data
                if existing_vote:
                    supabase.table("post_votes")\
                        .update({"vote_type": db_vote_value})\
                        .eq("vote_id", existing_vote["vote_id"])\
                        .execute()
                    user_vote = vote_type
            else:
                raise e

    # Compute net votes
    votes_resp = supabase.table("post_votes").select("vote_type").eq("post_id", post_id).execute()
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
        course = request.POST.get("course", "").strip()  # just text

        # Validate
        if not title or not description or not post_type or not course:
            return render(request, "create-post-text.html", {
                "error": "All fields are required.",
                "title": title,
                "description": description,
                "post_type": post_type,
                "course": course
            })

        # Insert post (course just a string)
        try:
            supabase.table("posts").insert({
                "title": title,
                "description": description,
                "content": "",
                "post_type": post_type,
                "user_id": user_id,
                "course_id": None  # leave null, just like Images & Video
            }).execute()

            return render(request, "create-post-text.html", {
                "success": "Post created successfully!",
                "title": "",
                "description": "",
                "post_type": "",
                "course": ""
            })

        except Exception as e:
            return render(request, "create-post-text.html", {
                "error": f"Error creating post: {str(e)}",
                "title": title,
                "description": description,
                "post_type": post_type,
                "course": course
            })

    return render(request, "create-post-text.html", {
        "profile_picture_url": profile_picture_url
    })

# --------------------------
# Create Post - Image/Video
# --------------------------
from django.conf import settings

def create_post_image(request):
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
        course = request.POST.get("course", "").strip()
        uploaded_file = request.FILES.get("fileUpload")

        # Validate fields (course required but NOT inserted into posts table)
        if not title or not post_type or not course or not uploaded_file:
            return render(request, "create-post-image-video.html", {
                "error": "All fields are required.",
                "title": title,
                "description": description,
                "post_type": post_type,
                "course": course,
            })

        # Upload to Supabase Storage
        try:
            file_path = f"{user_email}/{uploaded_file.name}"
            # read bytes (uploaded_file may be InMemoryUploadedFile or TemporaryUploadedFile)
            file_bytes = uploaded_file.read()
            supabase.storage.from_(settings.SUPABASE_BUCKET).upload(file_path, file_bytes)
            file_url = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(file_path).split("?")[0]
        except Exception as e:
            return render(request, "create-post-image-video.html", {
                "error": f"File upload failed: {str(e)}",
                "title": title,
                "description": description,
                "post_type": post_type,
                "course": course,
            })

        # Insert post record (DO NOT include `course` in insert unless your table has that column)
        try:
            supabase.table("posts").insert({
                "title": title,
                "description": description,
                "content": file_url,
                "post_type": post_type,
                "user_id": user_id
            }).execute()

            # determine preview type for template (image/video)
            preview_type = "video" if uploaded_file.content_type.startswith("video") else "image"

            return render(request, "create-post-image-video.html", {
                "success": "Post created successfully!",
                "preview_url": file_url,
                "preview_type": preview_type,
                # keep other values blank so form looks clean after success
                "title": "",
                "description": "",
                "post_type": "",
                "course": ""
            })

        except Exception as e:
            return render(request, "create-post-image-video.html", {
                "error": f"Error creating post: {str(e)}",
                "title": title,
                "description": description,
                "post_type": post_type,
                "course": course,
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

    user_email = request.session.get("user_email")
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
        url = request.POST.get("url", "").strip()

        if not title or not post_type or not url:
            return render(request, "create-post-link.html", {"error": "All fields are required."})

        try:
            supabase.table("posts").insert({
                "title": title,
                "description": description,
                "content": url,
                "post_type": post_type,
                "user_id": user_id
            }).execute()
            return render(request, "create-post-link.html", {"success": "Link post created successfully!"})
        except Exception as e:
            return render(request, "create-post-link.html", {"error": f"Error creating post: {str(e)}"})

    return render(request, "create-post-link.html", {
        "profile_picture_url": profile_picture_url
    })

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
                                    supabase.storage.from_(bucket).upload(pth, b"", file_options={"contentType": "application/octet-stream", "upsert": True})
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
        course_name = post.get("course_id") or "null"
        description = post.get("description", "")
        post_id = post.get("post_id")

        is_image = url.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
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
            "course": f"c/{course_name}",
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
        "profile_picture_url": profile_picture_url
    })

# --------------------------
# Logout
# --------------------------
def logout_page(request):
    request.session.flush()
    return redirect("/login/")
