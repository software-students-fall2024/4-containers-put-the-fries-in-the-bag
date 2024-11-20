"""
Unit tests for the web_app module.
"""

# pylint: disable=redefined-outer-name

import io
import pytest
import requests
import bcrypt
from web_app.web_app import app


@pytest.fixture
def client():
    """Set up a test client for Flask."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_login_success(client, monkeypatch):
    """Test the /login endpoint with valid credentials."""

    def mock_find_one(_query):
        return {
            "username": "testuser",
            "password": bcrypt.hashpw("testpass".encode("utf-8"), bcrypt.gensalt()),
        }

    monkeypatch.setattr("web_app.web_app.users_collection.find_one", mock_find_one)

    response = client.post(
        "/login",
        data={"username": "testuser", "password": "testpass"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Welcome" in response.data


def test_login_failure(client, monkeypatch):
    """Test the /login endpoint with invalid credentials."""

    def mock_find_one(_query):
        return {
            "username": "testuser",
            "password": bcrypt.hashpw("testpass".encode("utf-8"), bcrypt.gensalt()),
        }

    monkeypatch.setattr("web_app.web_app.users_collection.find_one", mock_find_one)

    response = client.post(
        "/login",
        data={"username": "testuser", "password": "wrongpass"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_register_new_user(client, monkeypatch):
    """Test the /register endpoint with a new user."""

    def mock_find_one(_query):
        return None

    def mock_insert_one(_document):
        pass

    monkeypatch.setattr("web_app.web_app.users_collection.find_one", mock_find_one)
    monkeypatch.setattr("web_app.web_app.users_collection.insert_one", mock_insert_one)

    response = client.post(
        "/register",
        data={"username": "newuser", "password": "newpass"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Registration successful! Please log in." in response.data


def test_register_existing_user(client, monkeypatch):
    """Test the /register endpoint with an existing user."""

    def mock_find_one(_query):
        return {"username": "existinguser"}

    monkeypatch.setattr("web_app.web_app.users_collection.find_one", mock_find_one)

    response = client.post(
        "/register",
        data={"username": "existinguser", "password": "newpass"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Username already exists" in response.data


def test_logout(client):
    """Test the /logout endpoint."""
    with client.session_transaction() as session:
        session["username"] = "testuser"

    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"login" in response.data


def test_homepage_redirect_without_login(client):
    """Test redirect to /login when accessing /homepage without a session."""
    response = client.get("/homepage", follow_redirects=True)
    assert response.status_code == 200
    assert b"login" in response.data


def test_capture_photo_without_image_data(client):
    """Test the /capture endpoint without providing image data."""
    with client.session_transaction() as session:
        session["username"] = "testuser"

    response = client.post("/capture", data={})
    assert response.status_code == 400
    assert response.get_json() == {"error": "No image uploaded"}


def test_capture_photo_unauthorized(client):
    """Test the /capture endpoint without authentication."""
    response = client.post("/capture", data={})
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_analytics_unauthorized(client):
    """Test the /analytics endpoint without authentication."""
    response = client.get("/analytics")
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_capture_timeout(client, monkeypatch):
    """Test the /capture endpoint when the ML service times out."""

    def mock_post(*args, **kwargs):
        raise requests.exceptions.Timeout("The request timed out.")

    monkeypatch.setattr("requests.post", mock_post)

    with client.session_transaction() as session:
        session["username"] = "testuser"

    data = {"image": (io.BytesIO(b"fake_image_data"), "image.jpg")}
    response = client.post("/capture", data=data, content_type="multipart/form-data")
    assert response.status_code == 500
    assert response.get_json() == {"error": "Failed to process image"}


def test_history_unauthorized(client):
    """Test the /history endpoint without authentication."""
    response = client.get("/history")
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_history_empty(client, monkeypatch):
    """Test the /history endpoint when no history exists."""

    def mock_find(_query):
        return iter([])

    monkeypatch.setattr("web_app.web_app.db.history.find", mock_find)

    with client.session_transaction() as session:
        session["username"] = "testuser"

    response = client.get("/history")
    assert response.status_code == 200
    assert response.get_json() == {"history": []}
