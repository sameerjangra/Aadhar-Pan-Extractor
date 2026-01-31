import cv2
import os
import uuid
import numpy as np

def extract_face(image_path, output_dir="temp_uploads"):
    """
    Detects and extracts the largest face from an image.
    Enforces a 35mm x 45mm aspect ratio (7:9).
    Returns the path to the cropped face image, or None if no face is found.
    """
    try:
        # Load the cascade
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
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        if len(faces) == 0:
            return None

        # Find the largest face
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = largest_face
        
        # Calculate target dimensions (35mm x 45mm aspect ratio)
        # Ratio = 35 / 45 = 0.777...
        target_ratio = 35.0 / 45.0
        
        # The detected face box (w, h) is usually just the face detected.
        # We need to include some hair and neck context.
        # Strategy:
        # 1. Base the crop width on the face width plus padding.
        #    Padding: 20% on each side -> 1.4x factor.
        
        crop_width = int(w * 1.4)
        crop_height = int(crop_width / target_ratio)
        
        # Determine center of the face
        face_cx = x + w // 2
        face_cy = y + h // 2
        
        # Determine crop coordinates (centered on face, maybe slightly shifted up to include hair?)
        # Face detection is usually centered on the face.
        # Passport photo: Eyes are above center. So we should shift the crop box UP relative to the face.
        # But 'face_cy' is detecting the 'face'.
        # Let's try centering first.
        
        crop_x1 = face_cx - crop_width // 2
        crop_y1 = face_cy - crop_height // 2
        
        # Adjustment: Shift up slightly (10% of height) to ensure chin isn't cut if we expanded height a lot
        # Actually, let's keep it centered to be safe against varying detection boxes.
        
        crop_x2 = crop_x1 + crop_width
        crop_y2 = crop_y1 + crop_height
        
        # Handle boundary conditions (if crop goes outside image)
        # We pad with black/white or just clamp?
        # Clamping destroys aspect ratio.
        # Better to pad the source image if needed, or just clamp and resize (might distort).
        # Let's simple clamp for now, but if we clamp, we must respect aspect ratio?
        # If strict 35x45 requested, we should Pad.
        
        img_h, img_w = img.shape[:2]
        
        # Pad image to handle out-of-bounds without cropping the crop
        pad_top = max(0, -crop_y1)
        pad_bottom = max(0, crop_y2 - img_h)
        pad_left = max(0, -crop_x1)
        pad_right = max(0, crop_x2 - img_w)
        
        if any([pad_top, pad_bottom, pad_left, pad_right]):
             img = cv2.copyMakeBorder(img, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_CONSTANT, value=[255, 255, 255])
             # Adjust coordinates
             crop_y1 += pad_top
             crop_y2 += pad_top
             crop_x1 += pad_left
             crop_x2 += pad_left

        cropped_face = img[crop_y1:crop_y2, crop_x1:crop_x2]
        
        # Resize to standard size?
        # 35mm x 45mm @ 300 DPI => ~413 x 531 pixels
        target_size = (413, 531)
        resized_face = cv2.resize(cropped_face, target_size, interpolation=cv2.INTER_AREA)

        # Save cropped image
        face_filename = f"face_{uuid.uuid4()}.jpg"
        face_path = os.path.join(output_dir, face_filename)
        
        os.makedirs(output_dir, exist_ok=True)
        cv2.imwrite(face_path, resized_face)
        return face_path

    except Exception as e:
        print(f"Error extracting face: {e}")
        return None
