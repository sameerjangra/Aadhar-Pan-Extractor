from face_extractor import extract_face
import os

img_path = "aadhar_sample.jpg"
if not os.path.exists(img_path):
    print("Sample image not found!")
    exit(1)

print(f"Testing extraction on {img_path}...")
result = extract_face(img_path)

if result:
    print(f"Success! Face extracted to: {result}")
else:
    print("Failure: No face detected.")
