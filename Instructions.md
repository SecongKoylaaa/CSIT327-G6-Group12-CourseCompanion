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
cd backend


Apply database migrations
python manage.py migrate


Run the development server
python manage.py runserver


Open the website in your browser
http://127.0.0.1:8000/


Example pages: /register/, /login/
