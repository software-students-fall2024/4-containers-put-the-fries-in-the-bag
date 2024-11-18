"""
Machine learning code for face recognition
"""

import os
import face_recognition


def load_character_encodings():
    """
    Load character encodings from images
    """
    encodings = []
    names = []
    path = "images"

    for file in os.listdir(path):
        if file.endswith(".jpg") or file.endswith(".png"):
            image_path = os.path.join(path, file)
            img = face_recognition.load_image_file(image_path)
            encoding = face_recognition.face_encodings(img)[0]
            encodings.append(encoding)
            names.append(
                file.split(".")[0]
            )  # Get the filename without extension, that will be the name of the character

    return encodings, names
