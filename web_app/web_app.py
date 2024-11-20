"""
This is the updated web application code.
"""

import os
import logging
from datetime import datetime, timezone
import pytz

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

# Configure logging
logging.basicConfig(level=logging.INFO)


@app.route("/")
def home():
    """Home page."""
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
    """Homepage for logged-in users."""
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("homepage.html", username=session["username"])


@app.route("/capture", methods=["POST"])
def capture():
    """Handle image capture and perform face matching."""
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files["image"]

    # Send image to ML client for face recognition
    try:
        response = requests.post(
            f"{ml_client_url}/recognize_face",
            files={
                "file": (
                    image_file.filename,
                    image_file.read(),
                    image_file.content_type,
                )
            },
            timeout=20,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        app.logger.error("Error communicating with ML service: %s", e)
        return jsonify({"error": "Failed to process image"}), 500

    result = response.json()
    if "error" in result:
        app.logger.error("Error occurred: %s", result["error"])
        return jsonify({"error": {"message": result["error"], "code": 400}}), 400

    matched_character = result.get("matched_character", "No match found")

    # Update analytics in the database
    user_analytics = db.analytics.find_one({"username": session["username"]})
    if not user_analytics:
        user_analytics = {"username": session["username"], "total": 0, "characters": {}}

    user_analytics["total"] += 1
    if matched_character in user_analytics["characters"]:
        user_analytics["characters"][matched_character] += 1
    else:
        user_analytics["characters"][matched_character] = 1

    db.analytics.update_one(
        {"username": session["username"]},
        {"$set": user_analytics},
        upsert=True,
    )

    # Save match history with UTC timestamp
    db.history.insert_one(
        {
            "username": session["username"],
            "matched_character": matched_character,
            "timestamp": datetime.now(timezone.utc),
        }
    )

    return jsonify({"match": matched_character})


@app.route("/history", methods=["GET"])
def history():
    """Retrieve match history for the logged-in user."""
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    eastern = pytz.timezone("America/New_York")
    history_records = db.history.find({"username": session["username"]}).sort(
        "timestamp", -1
    )
    history_list = []

    for record in history_records:
        timestamp = record["timestamp"]
        if isinstance(timestamp, str):
            dt_object = datetime.fromisoformat(timestamp)
        else:
            dt_object = timestamp

        local_time = dt_object.astimezone(eastern).strftime("%Y-%m-%d %H:%M:%S")
        history_list.append(
            {"character": record["matched_character"], "timestamp": local_time}
        )

    return jsonify({"history": history_list})


@app.route("/analytics", methods=["GET"])
def analytics():
    """Provide analytics data for the logged-in user."""
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_analytics_data = db.analytics.find_one({"username": session["username"]})
    if (
        not user_analytics_data
        or "characters" not in user_analytics_data
        or user_analytics_data["total"] == 0
    ):
        return jsonify({"data": []})

    data = [
        {
            "character": character,
            "percentage": (count / user_analytics_data["total"]) * 100,
        }
        for character, count in user_analytics_data["characters"].items()
    ]
    return jsonify({"data": data})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
