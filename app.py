from flask import Flask, render_template, request, redirect, url_for, flash
import bcrypt
import secrets

app = Flask(__name__)
app.secret_key = "supersecretkey"  # needed for flash messages

# --- Fake database ---
users = {}
reset_tokens = {}

# --- Routes ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"]
    if username in users:
        flash("Username already exists ❌")
    else:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        users[username] = hashed
        flash("✅ Registered successfully!")
    return redirect(url_for("home"))

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    if username not in users:
        flash("User not found ❌")
    elif bcrypt.checkpw(password.encode(), users[username]):
        flash("✅ Login successful!")
    else:
        flash("❌ Wrong password.")
    return redirect(url_for("home"))

@app.route("/request-reset", methods=["POST"])
def request_reset():
    username = request.form["username"]
    if username not in users:
        flash("User not found ❌")
    else:
        token = secrets.token_urlsafe(16)
        reset_tokens[token] = username
        flash(f"🔗 Password reset link: /reset/{token}")
    return redirect(url_for("home"))

@app.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    if token not in reset_tokens:
        return "❌ Invalid or expired reset link."
    if request.method == "POST":
        new_password = request.form["password"]
        username = reset_tokens[token]
        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
        users[username] = hashed
        del reset_tokens[token]
        flash("✅ Password reset successful!")
        return redirect(url_for("home"))
    return """
        <form method="POST">
            <input type="password" name="password" placeholder="New Password" required>
            <button type="submit">Reset Password</button>
        </form>
    """

if __name__ == "__main__":
    app.run(debug=True)
