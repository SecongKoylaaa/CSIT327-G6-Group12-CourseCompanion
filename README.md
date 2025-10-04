- Added Login Page (login.html) for user sign-in.

- Added Registration Page (register.html) for creating new accounts.

- Integrated Supabase with Django backend for user data storage.

- Implemented authentication: login checks Supabase to verify user credentials.

- Redirects users to home page upon successful login.



---

## ⚡ Setup Instructions

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd Course_Companion


Create and activate a virtual environment

python -m venv env
env\Scripts\activate          # Windows
# OR for Mac/Linux
# source env/bin/activate


Install dependencies
pip install -r requirements.txt


Navigate to Django project folder
cd backend\myproject


Apply database migrations
python manage.py migrate


Run the development server
python manage.py runserver


Open the website in your browser
http://127.0.0.1:8000/


Example pages: /register/, /login/
