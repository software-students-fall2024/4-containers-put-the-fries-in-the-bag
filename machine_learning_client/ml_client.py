"""
Optimized Machine Learning Service for Face Recognition
"""

import os
import logging
from flask import Flask, request, jsonify
import face_recognition
import numpy as np

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Global variables for encodings and names
ENCODINGS = []
NAMES = []
ENCODINGS_LOADED = False

IMAGES_PATH = "/app/images"
THRESHOLD = 0.8


def load_character_encodings():
    """
    Load character encodings from the specified images folder.
    Returns:
        tuple: A list of face encodings and corresponding names.
    """
    encodings = []
    names = []
    if not os.path.exists(IMAGES_PATH):
        logging.error("Images directory does not exist: %s", IMAGES_PATH)
        return encodings, names

    for filename in os.listdir(IMAGES_PATH):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            image_path = os.path.join(IMAGES_PATH, filename)
            try:
                image = face_recognition.load_image_file(image_path)
                face_enc = face_recognition.face_encodings(image)
                if face_enc:
                    encodings.append(face_enc[0])
                    names.append(os.path.splitext(filename)[0])  # Remove file extension
                    logging.info("Loaded encoding for: %s", filename)
                else:
                    logging.warning("No face found in image: %s", filename)
            except Exception as e:
                logging.error("Error loading image %s: %s", filename, e)
    return encodings, names


# Initialize encodings at module load
ENCODINGS, NAMES = load_character_encodings()
ENCODINGS_LOADED = True
logging.info("Character encodings loaded. Total: %d", len(ENCODINGS))


@app.route("/recognize_face", methods=["POST"])
def recognize_face():
    """
    Recognize face from an uploaded image.
    Returns:
        Response: JSON response with the matched character or an error message.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    try:
        # Load uploaded image
        test_image = face_recognition.load_image_file(file)
        test_encodings = face_recognition.face_encodings(test_image)

        if not test_encodings:
            return jsonify({"error": "No face found in the image"}), 400

        test_encoding = test_encodings[0]

        # Ensure encodings are preloaded
        if not ENCODINGS_LOADED:
            return jsonify({"error": "Encodings not loaded"}), 500

        # Compute face distances
        distances = face_recognition.face_distance(ENCODINGS, test_encoding)
        if len(distances) == 0:
            return jsonify({"matched_character": "No match found"})

        min_distance_index = np.argmin(distances)
        min_distance = distances[min_distance_index]

        # Check against threshold
        if min_distance > THRESHOLD:
            matched_character = "No match found"
        else:
            matched_character = NAMES[min_distance_index]

        logging.info("Matched character: %s with distance: %.2f", matched_character, min_distance)
        return jsonify({"matched_character": matched_character})
    except Exception as e:
        logging.error("Error during face recognition: %s", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
