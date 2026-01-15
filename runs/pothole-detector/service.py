import cv2
import time
import os
import random
import math
import datetime
import firebase_admin
import threading
from firebase_admin import credentials, firestore, storage
from ultralytics import YOLO
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
app = Flask(__name__)
CORS(app) # This allows your Netlify frontend to talk to this backend

@app.route('/')
def health_check():
    return "Argus AI Backend is Running!"


# --- Configuration ---
# Path to your Service Account Key (JSON file)
CRED_PATH = "pothole-detector-3f442-firebase-adminsdk-fbsvc-a1da9dffe4.json"
STORAGE_BUCKET = "pothole-detector-3f442.firebasestorage.app"  # From your config

# Model Path (Exported TFLite model)
MODEL_NAME = "yolov8n_float32.tflite" 
# Note: Ultralytics export often creates a folder or specific file naming.
# We will verify the exact name after export. If export fails, we fallback to .pt

CONFIDENCE_THRESHOLD = 0.4
REPORT_MIN_DISTANCE = 100 # meters

# TAMBARAM, CHENNAI COORDINATES (Starting Point)
CURRENT_LAT = 12.9229
CURRENT_LON = 80.1275

last_reported_lat = None
last_reported_lon = None

# --- Initialize Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate(CRED_PATH)
    firebase_admin.initialize_app(cred, {
        'storageBucket': STORAGE_BUCKET
    })

db = firestore.client()
bucket = storage.bucket()

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

def upload_image_to_firebase(image_path, filename):
    """Uploads image to Firebase Storage and returns the public URL."""
    try:
        blob = bucket.blob(f"events/{filename}")
        blob.upload_from_filename(image_path)
        # Make public (optional, or use signed URLs)
        blob.make_public()
        return blob.public_url
    except Exception as e:
        print(f"Error uploading image: {e}")
        return None

def encode_image_base64(image_path):
    """Encodes an image file to a Base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{encoded_string}"
    except Exception as e:
        print(f"Error encoding image base64: {e}")
        return None

def report_hazard(lat, lon, confidence, image_filename, local_image_path, is_simulated=False):
    """Writes hazard data to Firestore."""
    
    # 1. Upload Image (Optional)
    image_url = upload_image_to_firebase(local_image_path, image_filename)
    
    image_base64 = None
    if image_url is None:
        print(" [WARN] Image upload failed. Falling back to Base64 encoding in Firestore.")
        image_base64 = encode_image_base64(local_image_path)

    # 2. Add to Firestore
    timestamp = time.time()
    doc_ref = db.collection('hazards').document()
    
    data = {
        'id': doc_ref.id,
        'latitude': lat,
        'longitude': lon,
        'confidence': confidence,
        'image_url': image_url, # Store URL if available
        'image_base64': image_base64, # Store Base64 if URL failed
        'timestamp': timestamp,
        'created_at': firestore.SERVER_TIMESTAMP,
        'is_simulated': is_simulated  # Flag to trigger frontend warning
    }
    
    doc_ref.set(data)
    print(f" [REPORTED] Hazard logged to Firestore ID: {doc_ref.id} | Conf: {confidence:.2f} | Sim: {is_simulated}")

def main():
    # --- cloud simulation setup ---
    import os
    import sys
    import itertools
    import numpy as np

    # 1. ROBUST ENVIRONMENT CHECK
    # Check for 'RENDER' and other keys Render sets automatically
    IS_RENDER = (
        os.environ.get('RENDER') is not None or 
        os.environ.get('RENDER_SERVICE_ID') is not None or
        os.environ.get('RENDER_SERVICE_NAME') is not None
    )

    # Load model
    # Prioritize the custom trained model 'pothole_best.pt'
    MODEL_NAME = "pothole_best.pt" 
    print(f"Loading {MODEL_NAME}...")
    try:
        model = YOLO(MODEL_NAME)
    except Exception as e:
        print(f"Computed error loading model {MODEL_NAME}: {e}")
        print("Falling back to yolov8n.pt")
        model = YOLO("yolov8n.pt")    
        # If falling back to standard model, we must warn user it might detect generic objects
        print(" [WARN] Using generic model. Detections might not be accurate potholes.")

    # Initialize Video Source
    cap = None
    image_cycler = None
    
    # 2. HARDWARE FAILSAFE CHECK
    # If not explicitly on Render, try to open Webcam.
    if not IS_RENDER:
        print("System seemingly local. Attempting to access Webcam(0)...")
        try:
            # Squelch stderr for cleaner logs if it fails
            if os.name == 'posix': # Linux/Mac (Render is Linux)
                pass 
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print(" [WARN] Webcam(0) failed to open! Environment is likely Headless/Cloud.")
                print(" [INFO] Activating Failsafe: Switching to CLOUD SIMULATION MODE.")
                IS_RENDER = True # Force simulation
                cap = None # Ensure cap is cleared
        except Exception as e:
            print(f" [WARN] Webcam access error: {e}")
            print(" [INFO] Activating Failsafe: Switching to CLOUD SIMULATION MODE.")
            IS_RENDER = True

    # 3. CONFIGURE SIMULATION (If Explicitly Render OR Failsafe Triggered)
    if IS_RENDER:
        print("\n" + "!"*60)
        print("WARN: Running on Netlify/Render Cloud Platform (or Webcam failed).")
        print("WARN: Cannot access webcam!")
        print("WARN: Using sample images (download.webp, OIP.webp) for simulation.")
        print("!"*60 + "\n")

        # Load sample images from project root (../../)
        # Service.py is in runs/pothole-detector/
        
        # We need to find the project root. 
        # current file is in <root>/runs/pothole-detector/service.py
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        img_paths = [
            os.path.join(base_dir, "download.webp"),
            os.path.join(base_dir, "OIP.webp") 
        ]
        
        loaded_images = []
        for p in img_paths:
            if os.path.exists(p):
                img = cv2.imread(p)
                if img is not None:
                    loaded_images.append(img)
                else:
                    print(f" [ERR] Failed to load image: {p}")
            else:
                print(f" [ERR] Image not found: {p}")
        
        if not loaded_images:
            print(" [FATAL] No sample images found for Cloud Simulation. Exiting.")
            return

        print(f" [INFO] Loaded {len(loaded_images)} sample images for simulation.")
        image_cycler = itertools.cycle(loaded_images)

    print("Starting detection loop. Press 'q' to quit.")
    
    global last_reported_lat, last_reported_lon
    
    # We want to throttle reports not just by time, but by distance
    last_report_time = 0
    REPORT_COOLDOWN_TIME = 2.0 

    while True:
        if IS_RENDER:
            # Simulate frame reading from images
            frame = next(image_cycler)
            frame = frame.copy() # Ensure we don't modify the original cached image
            ret = True
            time.sleep(300) # Simulate ~10 FPS to not flood logs
        else:
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
                # Filter for class if needed, for now assume all detections are relevant
                detected = True
                max_conf = max(max_conf, conf)

        # Show feed ONLY if NOT on Render
        if not IS_RENDER:
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
                # Save event image locally first
                timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"event_{timestamp_str}.jpg"
                # Make sure events dir exists in runs/pothole-detector/events
                events_dir = "events"
                if not os.path.exists(events_dir):
                    os.makedirs(events_dir)
                    
                local_filepath = os.path.join(events_dir, filename)
                cv2.imwrite(local_filepath, annotated_frame)
                
                # Report to Firebase
                report_hazard(lat, lon, max_conf, filename, local_filepath, is_simulated=IS_RENDER)
                
                # Update last reported location
                last_reported_lat = lat
                last_reported_lon = lon
                last_report_time = current_time

        if not IS_RENDER:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            # On render, we just loop forever (or until killed)
            # Maybe yield a log every now and then to show it's alive
            if int(current_time) % 10 == 0:
                 pass # Keep logs clean, report_hazard already prints

    if cap:
        cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    # 1. Start the Detection/Simulation logic in a separate thread
    print("Starting background simulation thread...")
    threading.Thread(target=main, daemon=True).start()

    # 2. Start the Flask Server (This keeps Render happy by listening on the port)
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port)
