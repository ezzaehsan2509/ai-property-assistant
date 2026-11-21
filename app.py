import os

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for
)

from google import genai
from models import db, User


app = Flask(__name__)


# SECURITY CONFIGURATION
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY environment variable is not set."
    )


# DATABASE CONFIGURATION
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:

    if DATABASE_URL.startswith("postgresql+psycopg://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgresql+psycopg://",
            "postgresql+psycopg2://",
            1
        )

    elif DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql+psycopg2://",
            1
        )

    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgresql://",
            "postgresql+psycopg2://",
            1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# CREATE DATABASE TABLES
with app.app_context():
    db.create_all()


# GEMINI CONFIGURATION
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is not set."
    )

client = genai.Client(api_key=API_KEY)


# PROPERTY QUESTION CLASSIFIER
def is_property_question(question):

    prompt = f"""
You are a binary text classifier. Read the user's question.

If the question is about property, real estate, houses, apartments, land, plots,
renting, leasing, buying, selling, mortgages, ownership, housing societies,
property tax, or construction, output exactly: YES

Otherwise output exactly: NO

User question: {question}

Answer:
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        answer = response.text.strip().upper()

        print("Question:", question)
        print("Classifier Response:", repr(answer))

        return answer == "YES"

    except Exception as e:
        print(f"Classifier error: {e}")
        return False


# LANDING PAGE
@app.route("/")
def home():

    if "user" in session:
        return redirect(url_for("chat_page"))

    return render_template("home.html")


# LOGIN PAGE
@app.route("/login-page")
def login_page():

    if "user" in session:
        return redirect(url_for("chat_page"))

    return render_template("login.html")


# REGISTRATION PAGE
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    # REQUIRED FIELD VALIDATION
    if not name or not email or not password:
        return render_template(
            "register.html",
            error="Please fill in all fields."
        )

    # NAME VALIDATION
    if len(name) > 100:
        return render_template(
            "register.html",
            error="Name is too long."
        )

    # EMAIL VALIDATION
    if len(email) > 120 or "@" not in email:
        return render_template(
            "register.html",
            error="Please enter a valid email address."
        )

    # PASSWORD VALIDATION
    if len(password) < 8:
        return render_template(
            "register.html",
            error="Password must be at least 8 characters long."
        )

    # CHECK EXISTING USER
    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return render_template(
            "register.html",
            error="An account with this email already exists."
        )

    # CREATE NEW USER
    new_user = User(
        name=name,
        email=email,
        phone=""
    )

    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for("login_page"))


# LOGIN FUNCTION
@app.route("/login", methods=["POST"])
def login():

    email = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):

        session.clear()

        session["user"] = user.email
        session["user_id"] = user.id

        return redirect(url_for("chat_page"))

    return render_template(
        "login.html",
        error="Invalid email or password."
    )


# CHAT PAGE
@app.route("/chat-page")
def chat_page():

    if "user" not in session:
        return redirect(url_for("home"))

    return render_template("index.html")


# GEMINI CHAT API
@app.route("/chat", methods=["POST"])
def chat_api():

    if "user" not in session:
        return jsonify({
            "reply": "Please log in first."
        }), 401

    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({
            "reply": "No message received"
        }), 400

    user_message = data["message"]

    print("USER MESSAGE:", user_message)

    try:

        if not is_property_question(user_message):
            return jsonify({
                "reply": "I am an assistant specialized in real estate. Please ask something related to property."
            })

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=user_message
        )

        return jsonify({
            "reply": response.text
        })

    except Exception as e:

        print(f"Chat execution error: {e}")

        return jsonify({
            "reply": "An engine error occurred while processing your request."
        })


# LOGOUT
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# RUN FLASK
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )