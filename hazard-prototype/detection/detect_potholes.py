import cv2
import requests
import json
import time
import os
import random
import math
from ultralytics import YOLO
import datetime

# --- Configuration ---
BACKEND_URL = "http://localhost:5000/report_hazard"
EVENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'events')

# NOTE: ideally download a specific model like 'yolov8n-pothole.pt'
# For this prototype, we'll try to load a custom one if exists, else fallback to standard
# and we will filter for specific classes or just assume detection = pothole for the demo.
# If you have a .pt file trained on potholes, replace this path!
MODEL_NAME = "yolov8n.pt" 
# Try to load a specific one if available manually
if os.path.exists("pothole_best.pt"):
    MODEL_NAME = "pothole_best.pt"

CONFIDENCE_THRESHOLD = 0.4
REPORT_MIN_DISTANCE = 100 # meters

# TAMBARAM, CHENNAI COORDINATES (Starting Point)
CURRENT_LAT = 12.9229
CURRENT_LON = 80.1275

last_reported_lat = None
last_reported_lon = None

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates distance in meters between two lat/lon points."""
    R = 6371000 # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0)**2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def get_simulated_gps():
    """Simulates moving slightly in Chennai."""
    global CURRENT_LAT, CURRENT_LON
    
    # Move roughly 5-10 meters
    CURRENT_LAT += random.uniform(-0.00005, 0.00005)
    CURRENT_LON += random.uniform(-0.00005, 0.00005)
    
    return CURRENT_LAT, CURRENT_LON

def main():
    # Load model
    print(f"Loading {MODEL_NAME}...")
    try:
        model = YOLO(MODEL_NAME)
    except Exception as e:
        print(f"Computed error loading model {MODEL_NAME}: {e}")
        print("Falling back to yolov8n.pt")
        model = YOLO("yolov8n.pt")

    # Initialize Webcam (0)
    source = 0 
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print("Error: Could not open video source.")
        return

    print("Starting detection loop. Press 'q' to quit.")
    
    global last_reported_lat, last_reported_lon
    
    # We want to throttle reports not just by time, but by distance
    last_report_time = 0
    REPORT_COOLDOWN_TIME = 2.0 

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run inference
        results = model(frame, verbose=False)
        result = results[0]
        annotated_frame = result.plot()

        detected = False
        max_conf = 0.0
        
        # Check detections
        for box in result.boxes:
            conf = float(box.conf)
            if conf > CONFIDENCE_THRESHOLD:
                # OPTIONAL: Filter class here if using standard model
                # if model.names[int(box.cls)] in ['bowl', 'cup', 'car']: ...
                detected = True
                max_conf = max(max_conf, conf)

        # Show feed
        cv2.imshow("Pothole Detection (Chennai Prototype)", annotated_frame)

        # Logic to Report
        current_time = time.time()
        
        if detected and (current_time - last_report_time > REPORT_COOLDOWN_TIME):
            # 1. Get Location
            lat, lon = get_simulated_gps()
            
            # 2. Check Distance Constraint
            should_report = True
            if last_reported_lat is not None and last_reported_lon is not None:
                dist = haversine_distance(lat, lon, last_reported_lat, last_reported_lon)
                if dist < REPORT_MIN_DISTANCE:
                    print(f" [SKIP] Hazard detected but too close to previous tag ({dist:.1f}m < 100m)")
                    should_report = False
            
            if should_report:
                # Save event image
                timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"event_{timestamp_str}.jpg"
                filepath = os.path.join(EVENTS_DIR, filename)
                cv2.imwrite(filepath, annotated_frame)
                
                payload = {
                    "latitude": lat,
                    "longitude": lon,
                    "confidence": max_conf,
                    "image_filename": filename,
                    "timestamp": current_time
                }
                
                try:
                    resp = requests.post(BACKEND_URL, json=payload)
                    if resp.status_code == 201:
                        print(f" [REPORTED] Hazard at {lat:.5f}, {lon:.5f} | Conf: {max_conf:.2f}")
                        # Update last reported location
                        last_reported_lat = lat
                        last_reported_lon = lon
                        last_report_time = current_time
                    else:
                        print(f" [ERROR] Backend returned {resp.status_code}")
                except Exception as e:
                    print(f" [ERROR] Could not connect to backend: {e}")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
