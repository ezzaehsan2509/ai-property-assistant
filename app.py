import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from google import genai

app = Flask(__name__)

# Security configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

# Gemini configuration
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)


# ==========================================
# PROPERTY QUESTION CLASSIFIER
# ==========================================

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


# ==========================================
# LOGIN PAGE
# ==========================================

@app.route("/")
def home():

    if "user" in session:
        return redirect(url_for("chat_page"))

    return render_template("login.html")


# ==========================================
# LOGIN FUNCTION
# ==========================================

@app.route("/login", methods=["POST"])
def login():

    username = request.form.get("username")
    password = request.form.get("password")

    admin_username = os.environ.get("ADMIN_USERNAME")
    admin_password = os.environ.get("ADMIN_PASSWORD")

    if username == admin_username and password == admin_password:

        session["user"] = username

        return redirect(url_for("chat_page"))

    return render_template(
        "login.html",
        error="Invalid username or password."
    )


# ==========================================
# CHAT PAGE
# ==========================================

@app.route("/chat-page")
def chat_page():

    if "user" not in session:
        return redirect(url_for("home"))

    return render_template("index.html")


# ==========================================
# GEMINI CHAT API
# ==========================================

@app.route("/chat", methods=["POST"])
def chat_api():

    if "user" not in session:
        return jsonify({"reply": "Please log in first."}), 401

    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"reply": "No message received"}), 400

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


# ==========================================
# RUN FLASK
# ==========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )