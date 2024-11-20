"""
Machine learning code for face recognition
"""

# pylint: disable=broad-exception-caught

import os
import logging
import face_recognition
from flask import Flask, request, jsonify
import numpy as np

app = Flask(__name__)


def load_character_encodings():
    """Load character encodings from images folder."""
    encodings = []
    names = []
    images_path = "/app/images"

    for filename in os.listdir(images_path):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            image_path = os.path.join(images_path, filename)
            image = face_recognition.load_image_file(image_path)
            face_enc = face_recognition.face_encodings(image)
            if face_enc:
                encodings.append(face_enc[0])
                names.append(
                    os.path.splitext(filename)[0]
                )  # Filename without extension
                logging.debug("Loaded encoding for %s", filename)
            else:
                logging.warning("No face found in %s", filename)

    return encodings, names


@app.route("/recognize_face", methods=["POST"])
def recognize_face():
    """Recognize face from the uploaded image."""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    try:
        # Load the uploaded image
        test_image = face_recognition.load_image_file(file)
        test_encodings = face_recognition.face_encodings(test_image)
        if not test_encodings:
            return jsonify({"error": "No face found in the image"}), 400
        test_encoding = test_encodings[0]

        # Load stored encodings
        encodings, names = load_character_encodings()

        # Compute face distances
        distances = face_recognition.face_distance(encodings, test_encoding)
        if len(distances) == 0:
            matched_character = "No match found"
        else:
            min_distance_index = np.argmin(distances)
            min_distance = distances[min_distance_index]
            matched_character = names[min_distance_index]

            threshold = 0.8
            if min_distance > threshold:
                matched_character = "No match found"

        logging.debug(
            "Matched character: %s with distance: %s", matched_character, min_distance
        )
        return jsonify({"matched_character": matched_character})
    except Exception as e:
        logging.error("Error during face recognition: %s", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
