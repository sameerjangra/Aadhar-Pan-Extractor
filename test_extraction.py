import requests

url = "http://localhost:8000/extract/"
files = [
    ('files', ('aadhar_front.jpg', open('driving_licence_reference.jpg', 'rb'), 'image/jpeg')) # Dummy file reused
]
# This simulates uploading only one side. 
# Note: I am reusing driving_licence_reference.jpg but naming it aadhar to test logic if LLM sees it. 
# Actually, the LLM will see "Driving Licence" content and classify it as DL. This test might be tricky without real Aadhar images.
# But I can test the "PAN only" logic easily if I have a PAN image.
# I will try to upload the existing `driving_licence_reference.jpg` and see what it classifies as.
# If it's DL, and I don't upload PAN, it should pass (as DL doesn't require PAN).
# If I upload just "PAN", it should fail.

# Use existing file
try:
    with open('driving_licence_reference.jpg', 'rb') as f:
        response = requests.post(url, files={'files': ('test_dl.jpg', f, 'image/jpeg')})
        print(response.status_code)
        print(response.text)
except Exception as e:
    print(e)
