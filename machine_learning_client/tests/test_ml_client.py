"""
Unit tests for the machine_learning_client module
"""

# pylint: disable=redefined-outer-name

import io
from unittest.mock import patch
import pytest
from machine_learning_client.ml_client import app, load_character_encodings


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_load_character_encodings():
    """Test loading character encodings from images."""
    with patch("os.path.exists", return_value=True), patch(
        "os.listdir"
    ) as mock_listdir, patch(
        "face_recognition.load_image_file"
    ) as mock_load_image, patch(
        "face_recognition.face_encodings"
    ) as mock_encodings:
        mock_listdir.return_value = ["harry.jpg", "hermione.jpg"]
        mock_load_image.return_value = "mock_image"
        mock_encodings.side_effect = [
            [b"mock_encoding_harry"],
            [b"mock_encoding_hermione"],
        ]

        encodings, names = load_character_encodings()

        assert len(encodings) == 2
        assert len(names) == 2
        assert names == ["harry", "hermione"]


def test_recognize_face_no_file(client):
    """Test the recognize_face endpoint with no file provided."""
    response = client.post("/recognize_face")
    assert response.status_code == 400
    assert b"No file part" in response.data


def test_recognize_face_no_face_found(client, monkeypatch):
    """Test the recognize_face endpoint when no face is found in the image."""

    def mock_load_image_file(_file):
        """Mock load image file function."""
        return "mock_image"

    def mock_face_encodings(_image):
        """Mock face encodings function."""
        return []

    monkeypatch.setattr("face_recognition.load_image_file", mock_load_image_file)
    monkeypatch.setattr("face_recognition.face_encodings", mock_face_encodings)

    data = {"file": (io.BytesIO(b"fake_image_data"), "image.jpg")}
    response = client.post(
        "/recognize_face", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 400
    assert b"No face found in the image" in response.data


def test_recognize_face_successful_match(client, monkeypatch):
    """Test the recognize_face endpoint with a successful face match."""

    def mock_load_image_file(_file):
        """Mock load image file function."""
        return "mock_image"

    def mock_face_encodings(_image):
        """Mock face encodings function."""
        return [b"mock_test_encoding"]

    monkeypatch.setattr("face_recognition.load_image_file", mock_load_image_file)
    monkeypatch.setattr("face_recognition.face_encodings", mock_face_encodings)

    monkeypatch.setattr(
        "machine_learning_client.ml_client.ENCODINGS", [b"mock_test_encoding"]
    )
    monkeypatch.setattr("machine_learning_client.ml_client.NAMES", ["Harry Potter"])

    def mock_face_distance(_encodings, _test_encoding):
        """Mock face distance function."""
        return [0.2]

    monkeypatch.setattr("face_recognition.face_distance", mock_face_distance)

    data = {"file": (io.BytesIO(b"fake_image_data"), "image.jpg")}
    response = client.post(
        "/recognize_face", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 200
    assert b"Harry Potter" in response.data


def test_recognize_face_no_match(client, monkeypatch):
    """Test the recognize_face endpoint when no match is found."""

    def mock_load_image_file(_file):
        """Mock load image file function."""
        return "mock_image"

    def mock_face_encodings(_image):
        """Mock face encodings function."""
        return [b"mock_test_encoding"]

    def mock_load_character_encodings():
        """Mock load character encodings function."""
        return [b"mock_different_encoding"], ["Hermione Granger"]

    def mock_face_distance(_encodings, _test_encoding):
        """Mock face distance function."""
        return [0.9]  # Above threshold

    monkeypatch.setattr("face_recognition.load_image_file", mock_load_image_file)
    monkeypatch.setattr("face_recognition.face_encodings", mock_face_encodings)
    monkeypatch.setattr(
        "machine_learning_client.ml_client.load_character_encodings",
        mock_load_character_encodings,
    )
    monkeypatch.setattr("face_recognition.face_distance", mock_face_distance)

    data = {"file": (io.BytesIO(b"fake_image_data"), "image.jpg")}
    response = client.post(
        "/recognize_face", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 200
    assert b"No match found" in response.data


def test_recognize_face_invalid_image(client, monkeypatch):
    """Test the recognize_face endpoint when the uploaded file is not a valid image."""

    def mock_load_image_file(_file):
        """Mock load image file function."""
        raise ValueError("Invalid image file")

    monkeypatch.setattr("face_recognition.load_image_file", mock_load_image_file)

    data = {"file": (io.BytesIO(b"invalid_image_data"), "image.jpg")}
    response = client.post(
        "/recognize_face", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 500
    assert b"Invalid image file" in response.data


def test_recognize_face_multiple_faces(client, monkeypatch):
    """Test the recognize_face endpoint with an image containing multiple faces."""

    def mock_load_image_file(_file):
        """Mock load image file function."""
        return "mock_image"

    def mock_face_encodings(_image):
        """Mock face encodings function."""
        return [b"mock_face_1", b"mock_face_2"]

    def mock_face_distance(_encodings, _test_encoding):
        """Mock face distance function."""
        return [0.3, 0.4]

    monkeypatch.setattr("face_recognition.load_image_file", mock_load_image_file)
    monkeypatch.setattr("face_recognition.face_encodings", mock_face_encodings)
    monkeypatch.setattr("face_recognition.face_distance", mock_face_distance)

    monkeypatch.setattr("machine_learning_client.ml_client.ENCODINGS", [b"mock_face_1"])
    monkeypatch.setattr("machine_learning_client.ml_client.NAMES", ["Character 1"])

    data = {"file": (io.BytesIO(b"image_data"), "image.jpg")}
    response = client.post(
        "/recognize_face", data=data, content_type="multipart/form-data"
    )

    assert response.status_code == 200
    assert b"Character 1" in response.data
