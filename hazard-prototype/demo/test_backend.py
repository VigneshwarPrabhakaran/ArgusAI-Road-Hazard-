import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_backend():
    print("Testing Backend...")
    
    # 1. Test GET /hazards (should be empty initially)
    try:
        resp = requests.get(f"{BASE_URL}/hazards")
        print(f"GET /hazards: {resp.status_code}")
        assert resp.status_code == 200
        print(" -> Initial payload:", resp.json())
    except Exception as e:
        print(f"FAILED to connect: {e}")
        return

    # 2. Test POST /report_hazard
    payload = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "confidence": 0.85,
        "image_filename": "test.jpg",
        "timestamp": time.time()
    }
    try:
        resp = requests.post(f"{BASE_URL}/report_hazard", json=payload)
        print(f"POST /report_hazard: {resp.status_code}")
        assert resp.status_code == 201
        print(" -> Response:", resp.json())
    except Exception as e:
        print(f"FAILED to post: {e}")
        return

    # 3. Verify it was stored
    resp = requests.get(f"{BASE_URL}/hazards")
    data = resp.json()
    print(f"Final GET /hazards count: {len(data)}")
    assert len(data) > 0
    print(" -> Data:", data)
    
    print("SUCCESS: Backend is working!")

if __name__ == "__main__":
    time.sleep(2) # Wait for server startup
    test_backend()
