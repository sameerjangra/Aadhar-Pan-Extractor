import cv2
import os
import uuid
import numpy as np

def extract_face(image_path, output_dir="temp_uploads"):
    """
    Detects and extracts the largest face from an image.
    Returns the path to the cropped face image, or None if no face is found.
    """
    try:
        # Load the cascade
        # We need the xml file. Since we don't have it locally, we can use the one included in cv2 data if available,
        # or we might need to rely on the fact that cv2 usually bundles it.
        # cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        
        face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(face_cascade_path)
        
        if face_cascade.empty():
            print("Error: Face cascade classifier not loaded.")
            return None

        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            print(f"Error: Could not read image {image_path}")
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect faces
        # ScaleFactor: 1.1, MinNeighbors: 5 (Higher for less false positives)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        if len(faces) == 0:
            # Try looser parameters if strict failed?
            # Or just return None. ID photos are usually clear.
            # print("No faces detected.")
            return None

        # Find the largest face (assuming it's the ID photo)
        # Use (x, y, w, h)
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = largest_face
        
        # Add some padding? ID photos are usually tight crops.
        # Let's keep it tight or add tiny margin.
        margin = int(w * 0.1)
        x_start = max(0, x - margin)
        y_start = max(0, y - margin)
        x_end = min(img.shape[1], x + w + margin)
        y_end = min(img.shape[0], y + h + margin)

        cropped_face = img[y_start:y_end, x_start:x_end]
        
        # Save cropped image
        face_filename = f"face_{uuid.uuid4()}.jpg"
        face_path = os.path.join(output_dir, face_filename)
        
        # Ensure dir exists
        os.makedirs(output_dir, exist_ok=True)
        
        cv2.imwrite(face_path, cropped_face)
        return face_path

    except Exception as e:
        print(f"Error extracting face: {e}")
        return None
