# Road Hazard Detection System (AI + Google Maps SDK)

An AI-powered system to detect **unreported road hazards** such as potholes and unmarked speed breakers, and surface them directly inside a navigation experience built using **Google Maps SDK**.

---

## 📌 Problem Statement

Many critical road hazards — especially **potholes and unmarked speed breakers** — remain **unreported** in navigation apps.

Why this is a real problem:
- These hazards are not always severe enough for users to manually report
- Manual reporting is delayed and inconsistent
- Drivers encounter hazards *after* it’s too late to react
- Causes a Catastrophic effect on Human Lives

As a result, existing navigation systems provide **accurate routing but poor hazard awareness**.

---

## 💡 Our Approach (What We Actually Built)

This system acts as an **AI-powered hazard detection backend** that integrates seamlessly with an app using **Google Maps SDK**.

Key idea:
> *Let Google Maps handle navigation.  
We handle unreported hazard intelligence.*

---

## 🧠 What Hazards We Focus On

This project is intentionally **narrow in scope** to improve accuracy.

Currently supported hazards:
- **Potholes**
- **Unmarked speed breakers**
- **Road surface anomalies** (sudden elevation changes)


## 🚀 Core Features

- **Automatic Hazard Detection**  
  AI models detect road surface hazards from mobile or dashcam video feeds.

- **Real-Time Processing Pipeline**  
  Detected hazards are processed and stored with minimal latency.

- **Route-Aware Hazard Overlay**  
  Hazards are surfaced **only when they lie along the user’s current route**.

- **Google Maps SDK-Based Navigation**  
  The app uses the same navigation experience as Google Maps — no custom routing engine.

- **Deduplicated & Validated Data**  
  Multiple detections of the same hazard are clustered to avoid noise.

- **Privacy-First Design**  
  No raw video storage. Sensitive visual data is anonymized.

---

## 🏗️ System Architecture

### High-Level Flow

1. **Video Input**
   - Mobile camera or dashcam captures road footage

2. **AI Inference (Vertex AI)**
   - Computer vision model detects unreported hazards

3. **Backend API (Cloud Run)**
   - Receives detections
   - Attaches geo-coordinates
   - Applies validation logic

4. **Database (Firestore)**
   - Stores confirmed hazard locations
   - Supports real-time reads

5. **Mobile App (Google Maps SDK)**
   - Uses standard Google Maps navigation
   - Overlays hazard indicators along the active route

---

## 🛠️ Technologies Used

### Backend & AI
- **Vertex AI** – Computer vision inference
- **Cloud Run** – Serverless REST API
- **Cloud Functions** – Optional validation & clustering logic
- **Firestore** – Real-time hazard storage

### Maps & Navigation
- **Google Maps SDK (Android / Web)** – Navigation & map rendering
- **Routes API (optional)** – Route geometry for hazard matching

### Privacy & Security
- **Vision API** – Face & number plate anonymization
- **IAM** – Secure service-to-service communication

---

## 📱 App Behavior (Important Clarification)

- Navigation UI and routing are **entirely powered by Google Maps SDK**
- The system **does not modify routes**
- It **augments the route** with:
  - Hazard presence
  - Hazard warnings
  - Visual indicators ahead of the user

This ensures:
- Familiar user experience
- High reliability
- No reinvention of navigation logic

---

## 📊 Use Cases

- Drivers being warned of potholes *before* reaching them
- Two-wheeler riders avoiding sudden speed breakers
- Safer driving in poorly mapped urban and rural roads
- Data-driven insights for future road maintenance

---

## 🔮 Future Improvements (Realistic, Not Hype)

- **Edge Inference**  
  Partial on-device detection to reduce cloud latency

- **Severity Classification**  
  Distinguish shallow vs deep potholes

- **Temporal Validation**  
  Auto-expire hazards after repeated non-detections

- **Municipal Data Sharing**  
  Optional dashboards for road authorities

---

## 👥 Team

**Team Name:** Team Zypher  
**Team Leader:** Thiruvel S
**Team Member:** Vigneshwar P
**Problem Track:** Open Innovation  

---

## 📄 License

This project is currently a **prototype / academic submission**.  
License to be defined upon production deployment.
