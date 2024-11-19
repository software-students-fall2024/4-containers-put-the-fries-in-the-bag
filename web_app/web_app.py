"""
This is the web application code.
"""

import os
import base64
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from pymongo import MongoClient
from dotenv import load_dotenv
import bcrypt
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "SECRET_KEY")
app.config["SESSION_PERMANENT"] = False

mongo_uri = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
client = MongoClient(mongo_uri)
db = client["harryface"]
users_collection = db["users"]

ml_client_url = "http://ml-client:5000"


@app.route("/")
def home():
    """This is the home page."""
    if "username" in session:
        return redirect(url_for("homepage"))
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log in page for registered users."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")

        user = users_collection.find_one({"username": username})
        if user and bcrypt.checkpw(password, user["password"]):
            session["username"] = username
            session.permanent = False
            return redirect(url_for("homepage"))
        flash("Invalid username or password. Please try again.")
        return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registration page for new users."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")

        if users_collection.find_one({"username": username}):
            flash("Username already exists. Please choose a different one.")
        else:
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
            users_collection.insert_one(
                {"username": username, "password": hashed_password}
            )
            flash("Registration successful! Please log in.")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    """Logs user out and clears session."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/homepage")
def homepage():
    """This is the homepage for logged-in users."""
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("homepage.html", username=session["username"])


@app.route("/match_face", methods=["POST"])
def match_face():
    """Match a captured photo to the closest face image in the images folder."""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    image_data = file.read()
    try:
        response = requests.post(
            f"{ml_client_url}/recognize_face",
            files={"file": ("image.jpg", image_data, "image/jpeg")},
            timeout=10,  # Add a timeout of 10 seconds
        )
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

    result = response.json()
    if "error" in result:
        return jsonify({"error": result["error"]}), 400
    return jsonify(result)


@app.route("/capture", methods=["POST"])
def capture():
    """Handle image capture and perform face matching."""
    data = request.get_json()
    image_data = data.get("image")

    if not image_data:
        return jsonify({"error": "No image data received"}), 400

    # Decode base64 image data
    header, encoded = image_data.split(",", 1)
    image_bytes = base64.b64decode(encoded)

    # Send image to ML client for face recognition
    try:
        response = requests.post(
            f"{ml_client_url}/recognize_face",
            files={"file": ("capture.png", image_bytes, "image/png")},
            timeout=10,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

    result = response.json()
    if "error" in result:
        return jsonify({"error": result["error"]}), 400

    matched_character = result.get("matched_character", "No match found")

    return jsonify({"match": matched_character})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
