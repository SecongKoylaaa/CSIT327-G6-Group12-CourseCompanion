from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime, timezone, timedelta
from supabase import create_client
import time
import secrets

# --------------------------
# Initialize Supabase client
# --------------------------
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

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
# Registration View
# --------------------------
def register_page(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirmPassword", "").strip()
        username = request.POST.get("username", "").strip()
        role = request.POST.get("role", "").strip().lower()

        # ---------- Validation ----------
        if not email or not password or not confirm_password or not role:
            return render(request, "register.html", {"error": "All fields are required."})
        if password != confirm_password:
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

    # GET request
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

        # Update last_login timestamp
        try:
            supabase.table("users").update({
                "last_login": datetime.now(timezone.utc).isoformat()
            }).eq("id", user["id"]).execute()
        except Exception as e:
            print(f"Warning: failed to update last_login: {e}")

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
            "reset_link": reset_link
        })

    return render(request, "recover_password.html", {"email": email})



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

        return render(request, "reset_password.html", {"message": "Password reset successful! You can now log in."})

    return render(request, "reset_password.html", {"reset_token": reset_token})


## --------------------------
# Home View (Protected)
# --------------------------

def home_page(request):
    if "user_email" not in request.session:
        return redirect("/login/")

    user_email = request.session.get("user_email")

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
    response = supabase.table("posts").select("*").order("created_at", desc=True).execute()
    posts = response.data if response.data else []

    # Get current user ID for vote detection
    user_id = None
    if user_email:
        user_resp = supabase.table("users").select("id").eq("email", user_email).maybe_single().execute()
        if user_resp.data:
            user_id = user_resp.data["id"]

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
        votes_resp = supabase.table("post_votes").select("*").eq("post_id", post_id).execute()
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

        # -----------------------------
        # Fetch all comments for this post
        # -----------------------------
        comment_resp = supabase.table("comments").select("*").eq("post_id", post_id).order("created_at", desc=False).execute()
        all_comments = comment_resp.data if comment_resp.data else []

        # -----------------------------
        # Build nested comment tree
        # -----------------------------
        def build_comment_tree(comments, parent_id_val=None):
            tree = []
            for c in comments:
                if c.get("parent_id") == parent_id_val:
                    user_resp = supabase.table("users").select("email").eq("id", c["user_id"]).maybe_single().execute()
                    author_email = user_resp.data["email"] if user_resp.data and "email" in user_resp.data else "anonymous@example.com"

                    votes_resp = supabase.table("comment_votes").select("*").eq("comment_id", c["comment_id"]).execute()
                    votes = votes_resp.data or []

                    upvotes_c = len([v for v in votes if v["vote_type"] == "upvote"])
                    downvotes_c = len([v for v in votes if v["vote_type"] == "downvote"])
                    net_votes_c = upvotes_c - downvotes_c

                    user_vote_c = None
                    if user_id:
                        uv_c = next((v["vote_type"] for v in votes if v["user_id"] == user_id), None)
                        if uv_c == "upvote":
                            user_vote_c = "upvote"
                        elif uv_c == "downvote":
                            user_vote_c = "downvote"

                    comment_obj = {
                        "comment_id": c["comment_id"],
                        "author": author_email,
                        "text": c["text"],
                        "created_at": time_since(c["created_at"]),
                        "edited": c.get("edited", False),
                        "upvote_count": upvotes_c,
                        "downvote_count": downvotes_c,
                        "net_votes": net_votes_c,
                        "user_vote": user_vote_c,
                        "replies": build_comment_tree(comments, c["comment_id"])
                    }
                    tree.append(comment_obj)
            return tree

        nested_comments = build_comment_tree(all_comments)

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
            "comment_count": len(all_comments)
        })

    return render(request, "home.html", {
        "user_email": user_email,
        "role": request.session.get("role", "student"),
        "posts": formatted_posts,
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
    user_resp = supabase.table("users").select("id").eq("email", user_email).maybe_single().execute()
    if not user_resp.data:
        return JsonResponse({"error": "User not found"}, status=404)
    user_id = user_resp.data["id"]

    # Check existing vote
    existing_vote_resp = supabase.table("comment_votes")\
        .select("*").eq("comment_id", comment_id).eq("user_id", user_id).maybe_single().execute()
    existing_vote = existing_vote_resp.data if existing_vote_resp and existing_vote_resp.data else None

    if existing_vote:
        if existing_vote["vote_type"] == vote_type:
            supabase.table("comment_votes").delete().eq("vote_id", existing_vote["vote_id"]).execute()
            user_vote = None
        else:
            supabase.table("comment_votes").update({"vote_type": vote_type}).eq("vote_id", existing_vote["vote_id"]).execute()
            user_vote = vote_type
    else:
        supabase.table("comment_votes").insert({
            "user_id": user_id,
            "comment_id": comment_id,
            "vote_type": vote_type
        }).execute()
        user_vote = vote_type

    # Compute net votes
    votes_resp = supabase.table("comment_votes").select("*").eq("comment_id", comment_id).execute()
    votes = votes_resp.data or []
    net_votes = sum(1 if v["vote_type"] == "upvote" else -1 for v in votes)

    return JsonResponse({"net_votes": net_votes, "user_vote": user_vote})


# --------------------------
# Post Voting
# --------------------------
FRONTEND_TO_DB = {"upvote": "up", "downvote": "down"}

@csrf_exempt
def vote_post(request, post_id, vote_type):
    if "user_email" not in request.session:
        return JsonResponse({"error": "Login required"}, status=403)

    user_email = request.session.get("user_email")
    user_resp = supabase.table("users").select("id").eq("email", user_email).maybe_single().execute()
    if not user_resp.data:
        return JsonResponse({"error": "User not found"}, status=404)
    user_id = user_resp.data["id"]

    if vote_type not in FRONTEND_TO_DB:
        return JsonResponse({"error": "Invalid vote type"}, status=400)
    db_vote_value = FRONTEND_TO_DB[vote_type]

    # Check post existence
    post_resp = supabase.table("posts").select("post_id").eq("post_id", post_id).maybe_single().execute()
    if not post_resp.data:
        return JsonResponse({"error": "Post not found"}, status=404)

    # Check existing vote
    existing_vote_resp = supabase.table("post_votes")\
        .select("*").eq("post_id", post_id).eq("user_id", user_id).maybe_single().execute()
    existing_vote = existing_vote_resp.data if existing_vote_resp and existing_vote_resp.data else None

    if existing_vote:
        if existing_vote.get("vote_type") == db_vote_value:
            supabase.table("post_votes").delete().eq("vote_id", existing_vote["vote_id"]).execute()
            user_vote = None
        else:
            supabase.table("post_votes").update({"vote_type": db_vote_value}).eq("vote_id", existing_vote["vote_id"]).execute()
            user_vote = vote_type
    else:
        try:
            supabase.table("post_votes").insert({
                "user_id": user_id,
                "post_id": post_id,
                "vote_type": db_vote_value
            }).execute()
            user_vote = vote_type
        except Exception as e:
            if "duplicate key value" in str(e):
                existing_vote_resp = supabase.table("post_votes")\
                    .select("*").eq("post_id", post_id).eq("user_id", user_id).maybe_single().execute()
                existing_vote = existing_vote_resp.data
                if existing_vote:
                    supabase.table("post_votes").update({"vote_type": db_vote_value}).eq("vote_id", existing_vote["vote_id"]).execute()
                    user_vote = vote_type
            else:
                raise e

        # Compute net votes using count (safe for many votes)
        up_resp = supabase.table("post_votes")\
            .select("vote_type", count="exact")\
            .eq("post_id", post_id)\
            .eq("vote_type", "up")\
            .execute()
        up_count = up_resp.count or 0

        down_resp = supabase.table("post_votes")\
            .select("vote_type", count="exact")\
            .eq("post_id", post_id)\
            .eq("vote_type", "down")\
            .execute()
        down_count = down_resp.count or 0

        net_votes = up_count - down_count


    return JsonResponse({"net_votes": net_votes, "user_vote": user_vote})


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

from django.shortcuts import render, redirect
from django.conf import settings

# --------------------------
# Create Post - Text
# --------------------------
def create_post_text(request):
    if "user_email" not in request.session:
        return redirect("/login/")

    user_email = request.session.get("user_email")
    user_resp = supabase.table("users").select("id").eq("email", user_email).execute()
    if not user_resp.data:
        return render(request, "create-post-text.html", {"error": "User not found."})

    user_id = user_resp.data[0]["id"]

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        post_type = request.POST.get("post_type", "").strip()
        url = request.POST.get("url", "").strip()

        if not title or not description or not post_type or not url:
            return render(request, "create-post-text.html", {"error": "All fields are required."})

        try:
            supabase.table("posts").insert({
                "title": title,
                "description": description,
                "content": url,  # Store link in content
                "post_type": post_type,
                "user_id": user_id
            }).execute()
            return render(request, "create-post-text.html", {"success": "Post created successfully!"})
        except Exception as e:
            return render(request, "create-post-text.html", {"error": f"Error creating post: {str(e)}"})

    return render(request, "create-post-text.html")


# --------------------------
# Create Post - Image/Video
# --------------------------
def create_post_image(request):
    if "user_email" not in request.session:
        return redirect("/login/")

    user_email = request.session.get("user_email")
    user_resp = supabase.table("users").select("id").eq("email", user_email).execute()
    if not user_resp.data:
        return render(request, "create-post-image-video.html", {"error": "User not found."})

    user_id = user_resp.data[0]["id"]

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        post_type = request.POST.get("post_type", "").strip()
        file = request.FILES.get("fileUpload")

        if not title or not description or not post_type or not file:
            return render(request, "create-post-image-video.html", {"error": "All fields are required."})

        try:
            # Upload file
            file_path = f"{user_email}/{file.name}"
            file_bytes = file.read()
            supabase.storage.from_(settings.SUPABASE_BUCKET).upload(file_path, file_bytes)
            file_url = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(file_path).rstrip("?")
        except Exception as e:
            return render(request, "create-post-image-video.html", {"error": f"File upload failed: {str(e)}"})

        try:
            supabase.table("posts").insert({
                "title": title,
                "description": description,
                "content": file_url,
                "post_type": post_type,
                "user_id": user_id
            }).execute()
            return render(request, "create-post-image-video.html", {"success": "Post created successfully!"})
        except Exception as e:
            return render(request, "create-post-image-video.html", {"error": f"Error creating post: {str(e)}"})

    return render(request, "create-post-image-video.html")


# --------------------------
# Create Post - Link
# --------------------------
def create_post_link(request):
    if "user_email" not in request.session:
        return redirect("/login/")

    user_email = request.session.get("user_email")
    user_resp = supabase.table("users").select("id").eq("email", user_email).execute()
    if not user_resp.data:
        return render(request, "create-post-link.html", {"error": "User not found."})

    user_id = user_resp.data[0]["id"]

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

    return render(request, "create-post-link.html")


# --------------------------
# Logout
# --------------------------
def logout_page(request):
    request.session.flush()
    return redirect("/login/")
