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
