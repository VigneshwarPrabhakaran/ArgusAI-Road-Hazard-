import os
import json
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

STORAGE_FILE = os.path.join(os.path.dirname(__file__), 'storage.json')
EVENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'events')

# Ensure events directory exists
if not os.path.exists(EVENTS_DIR):
    os.makedirs(EVENTS_DIR)

def load_hazards():
    if not os.path.exists(STORAGE_FILE):
        return []
    try:
        with open(STORAGE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading storage: {e}")
        return []

def save_hazards(hazards):
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(hazards, f, indent=4)
    except Exception as e:
        print(f"Error saving storage: {e}")

@app.route('/report_hazard', methods=['POST'])
def report_hazard():
    """
    Receives a hazard report.
    Expected JSON:
    {
        "latitude": float,
        "longitude": float,
        "confidence": float,
        "image_filename": string (optional),
        "timestamp": float (optional)
    }
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    hazards = load_hazards()
    
    new_hazard = {
        "id": len(hazards) + 1,
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "confidence": data.get("confidence"),
        "image_filename": data.get("image_filename"),
        "timestamp": data.get("timestamp", time.time())
    }
    
    hazards.append(new_hazard)
    save_hazards(hazards)
    
    print(f"Hazard reported: {new_hazard}")
    return jsonify({"message": "Hazard reported successfully", "hazard_id": new_hazard["id"]}), 201

@app.route('/hazards', methods=['GET'])
def get_hazards():
    """Returns the list of reported hazards."""
    hazards = load_hazards()
    return jsonify(hazards)

@app.route('/events/<path:filename>')
def serve_event_image(filename):
    """Serves the captured event images."""
    return send_from_directory(EVENTS_DIR, filename)

if __name__ == '__main__':
    print("Starting Backend Service...")
    # Run on 0.0.0.0 to be accessible, port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)
