"""
Unit tests for the web_app module.
"""

# pylint: disable=redefined-outer-name

import pytest
from web_app.web_app import app, users_collection
import io
from werkzeug.datastructures import FileStorage


class MockMongoCollection:
    """Mock MongoDB collection for testing database operations."""

    def __init__(self):
        """Initialize a mock database."""
        self.data = {}

    def find_one(self, query):
        """Simulate the MongoDB find_one method."""
        key = query.get("username")
        return self.data.get(key)

    def insert_one(self, document):
        """Simulate the MongoDB insert_one method."""
        self.data[document["username"]] = document


@pytest.fixture
def client(monkeypatch):
    """Set up mock database and client for testing."""
    mock_collection = MockMongoCollection()
    monkeypatch.setattr("web_app.web_app.users_collection", mock_collection)

    app.config["TESTING"] = True
    with app.app_context():
        with app.test_client() as client:
            yield client


def test_mock_database():
    """Test mock database."""
    mock_db = MockMongoCollection()
    mock_db.insert_one(
        {
            "username": "testuser",
            "password": b"$2b$12$KIX9B0O.NHih9kFya4mPQOm9lGjpdQbs51q8g8IWyPtQLcs4/1eS2",
        }
    )
    user = mock_db.find_one({"username": "testuser"})
    assert user is not None
    assert user["username"] == "testuser"


def test_home_page(client):
    """Test home page."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"login" in response.data


def test_register(client):
    """Test registration."""
    response = client.post(
        "/register",
        data={"username": "testuser", "password": "testpassword"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Registration successful! Please log in." in response.data


def test_register_existing_user(client):
    """Test registration with existing user."""
    client.post(
        "/register",
        data={"username": "testuser", "password": "testpassword"},
        follow_redirects=True,
    )
    response = client.post(
        "/register",
        data={"username": "testuser", "password": "anotherpassword"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Username already exists. Please choose a different one." in response.data


def test_homepage_access(client):
    """Test homepage access with valid session."""
    with client.session_transaction() as session:
        session["username"] = "testuser"

    response = client.get("/homepage")
    assert response.status_code == 200
    assert b"testuser" in response.data
    assert b"Welcome to HarryFace, testuser" in response.data  



def test_login_failure(client):
    """Test login with invalid credentials."""
    response = client.post(
        "/login",
        data={"username": "unknownuser", "password": "wrongpassword"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_register_and_login(client):
    """Test registration and login."""
    response = client.post(
        "/register",
        data={"username": "flowuser", "password": "flowpass"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Registration successful! Please log in." in response.data

    response = client.post(
        "/login",
        data={"username": "flowuser", "password": "flowpass"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Welcome to HarryFace, flowuser" in response.data  



def test_logout(client):
    """Test logout."""
    with client.session_transaction() as session:
        session["username"] = "testuser"
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"login" in response.data


def test_homepage_redirect(client):
    """Test homepage redirect with no session."""
    response = client.get("/homepage", follow_redirects=True)
    assert response.status_code == 200
    assert b"login" in response.data


def test_flash_message_display(client):
    """Test flash message display on login failure."""
    response = client.post(
        "/login",
        data={"username": "wronguser", "password": "wrongpass"},
        follow_redirects=True,
    )
    assert b"Invalid username or password. Please try again." in response.data

def test_capture_photo_without_image_data(client):
    """Test the capture endpoint without providing image data."""
    response = client.post("/capture", json={})
    assert response.status_code == 400
    assert b"No image data received" in response.data

def test_match_face_success(client, monkeypatch):
    """Test the match_face endpoint with a simulated successful response."""
    def mock_post(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
            def json(self):
                return {"matched_character": "Harry Potter"}
            def raise_for_status(self):
                pass  

        return MockResponse()

    monkeypatch.setattr("requests.post", mock_post)

    with client.session_transaction() as session:
        session["username"] = "testuser"

    data = {
        "file": (io.BytesIO(b"fake_image_data"), "image.jpg")
    }
    response = client.post("/match_face", data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert b"Harry Potter" in response.data


def test_protected_routes_redirect(client):
    """Test access to protected routes without login redirects to login page."""
    response = client.get("/homepage", follow_redirects=True)
    assert response.status_code == 200
    assert b"login" in response.data

def test_login_success(client):
    """Test successful login creates session and redirects to homepage."""
    client.post("/register", data={"username": "testloginuser", "password": "testloginpass"})

    response = client.post(
        "/login",
        data={"username": "testloginuser", "password": "testloginpass"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Welcome to HarryFace, testloginuser" in response.data  

