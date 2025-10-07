from django.shortcuts import render, redirect
from django.http import HttpResponse
from supabase import create_client
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password

# Initialize Supabase client
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# --------------------------
# Registration View
# --------------------------
def register_page(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        username = request.POST.get("username", "").strip()  # Optional field
        role = "student"  # Default role
        profile_picture = None  # Optional field (can be None)
        bio = None  # Optional field (can be None)
        last_login = None  # Optional field (can be None)

        # Ensure email and password are provided
        if not email or not password:
            return render(request, "register.html", {"error": "Email and password are required."})

        # Hash the password before inserting it into the database
        password_hash = make_password(password)

        # Check if email already exists in the database
        existing = supabase.table("users").select("*").eq("email", email).execute()
        if existing.data:
            return render(request, "register.html", {"error": "Account already exists. Please login."})

        # Insert the new user into the Supabase database
        try:
            response = supabase.table("users").insert({
                "email": email,
                "password_hash": password_hash,  # Store hashed password
                "role": role,
                "username": username,  # Optional
                "profile_picture": profile_picture,  # Optional (can be None)
                "bio": bio,  # Optional (can be None)
                "last_login": last_login,  # Optional (can be None)
                "date_joined": "now()"  # Set current timestamp for date_joined
            }).execute()

            if response.status_code != 201:
                return render(request, "register.html", {"error": f"Error registering: {response.error_message}"})

        except Exception as e:
            return render(request, "register.html", {"error": f"Error registering: {str(e)}"})

        # Redirect to login page after successful registration
        return redirect("/login")

    return render(request, "register.html")


# --------------------------
# Login View
# --------------------------
def login_page(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        # Ensure email and password are provided
        if not email or not password:
            return render(request, "login.html", {"error": "Email and password are required."})

        # Fetch user from Supabase
        try:
            response = supabase.table("users").select("*").eq("email", email).execute()
        except Exception as e:
            return render(request, "login.html", {"error": f"Error connecting to database: {str(e)}"})

        if not response.data:
            return render(request, "login.html", {"error": "No account found. Please register."})

        # Get the user data
        user = response.data[0]

        # Check if the provided password matches the stored hashed password
        if not check_password(password, user["password_hash"]):
            return render(request, "login.html", {"error": "Invalid credentials!"})

        # Login successful → Render home.html
        return render(request, "home.html", {"user_email": email, "role": user.get("role", "student")})

    return render(request, "login.html")
