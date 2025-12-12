"""
Test script to verify Supabase registration functionality
Run this with: python test_supabase_registration.py
"""
import os
import sys
from datetime import datetime, timezone
from django.contrib.auth.hashers import make_password

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()

from django.conf import settings
from supabase import create_client

# Initialize Supabase
SUPABASE_AUTH_KEY = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None) or settings.SUPABASE_KEY
supabase = create_client(settings.SUPABASE_URL, SUPABASE_AUTH_KEY)

print("=" * 60)
print("SUPABASE REGISTRATION TEST")
print("=" * 60)

# Test 1: Connection Test
print("\n[TEST 1] Testing Supabase connection...")
try:
    result = supabase.table("users").select("id").limit(1).execute()
    print("✓ Connection successful!")
    print(f"  Response: {result}")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    sys.exit(1)

# Test 2: Insert Test User
print("\n[TEST 2] Testing user insertion with username...")
test_email = f"test_{datetime.now().timestamp()}@example.com"
test_username = f"testuser_{int(datetime.now().timestamp())}"
test_password = "TestPassword123!"

user_data = {
    "email": test_email,
    "password_hash": make_password(test_password),
    "username": test_username,
    "role": "student",
    "profile_picture": None,
    "bio": None,
    "last_login": None,
    "date_joined": datetime.now(timezone.utc).isoformat(),
    "created_at": datetime.now(timezone.utc).isoformat()
}

print(f"  Inserting user: email={test_email}, username={test_username}")

try:
    response = supabase.table("users").insert(user_data).execute()
    
    if response and response.data:
        print("✓ User inserted successfully!")
        print(f"  User ID: {response.data[0].get('id')}")
        print(f"  Email: {response.data[0].get('email')}")
        print(f"  Username: {response.data[0].get('username')}")
        
        # Test 3: Verify username is in database
        print("\n[TEST 3] Verifying username in database...")
        verify = supabase.table("users").select("*").eq("username", test_username).execute()
        if verify and verify.data:
            print("✓ Username found in database!")
            print(f"  Retrieved user: {verify.data[0].get('email')} / {verify.data[0].get('username')}")
        else:
            print("✗ Username not found in database!")
            
    else:
        print(f"✗ Insert failed!")
        print(f"  Response: {response}")
        print(f"  Error: {getattr(response, 'error', None)}")
        
except Exception as e:
    print(f"✗ Exception during insert: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
