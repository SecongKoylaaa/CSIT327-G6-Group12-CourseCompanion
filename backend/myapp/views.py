from django.shortcuts import render, redirect
from django.http import HttpResponse
from supabase import create_client
from django.conf import settings

# Initialize Supabase client
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# --------------------------
# Registration View
# --------------------------
def register_page(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not email or not password:
            return render(request, "register.html", {"error": "Email and password are required."})

        role = "student"  # default role

        # Check if email already exists
        existing = supabase.table("users").select("*").eq("email", email).execute()
        if existing.data:
            return render(request, "register.html", {"error": "Account already exists. Please login."})

        # Insert user into Supabase
        try:
            supabase.table("users").insert({
                "email": email,
                "password": password,  # In production, hash the password!
                "role": role
            }).execute()
        except Exception as e:
            return render(request, "register.html", {"error": f"Error registering: {str(e)}"})

        return redirect("/login")  # redirect to login after successful registration

    return render(request, "register.html")


# --------------------------
# Login View
# --------------------------

def login_page(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not email or not password:
            return render(request, "login.html", {"error": "Email and password are required."})

        # Fetch user from Supabase
        try:
            response = supabase.table("users").select("*").eq("email", email).execute()
        except Exception as e:
            return render(request, "login.html", {"error": f"Error connecting to database: {str(e)}"})

        if not response.data:
            return render(request, "login.html", {"error": "No account found. Please register."})

        user = response.data[0]
        if user["password"] != password:
            return render(request, "login.html", {"error": "Invalid credentials!"})

        # Login successful → Render home.html
        return render(request, "home.html", {"user_email": email, "role": user.get("role", "student")})

    return render(request, "login.html")
