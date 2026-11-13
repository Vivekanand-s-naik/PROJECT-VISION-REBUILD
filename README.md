# ProjectVision: Autonomous Multi-Stream Vision, Biometrics & Security Platform

[![System Version](https://img.shields.io/badge/Version-2.0.0--Autonomous-blue.svg)](file:///d:/PROJECTS/ProjectVision)
[![Python](https://img.shields.io/badge/Python-3.11-green.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-36%20Passed-brightgreen.svg)](file:///d:/PROJECTS/ProjectVision/tests)
[![Platform](https://img.shields.io/badge/Architecture-Modular%20Pub--Sub-purple.svg)](file:///d:/PROJECTS/ProjectVision/core)

ProjectVision is a comprehensive, production-grade intelligent multi-camera computer vision, biometric attendance, and automated surveillance command center. It unifies deep learning vision pipelines, eye gaze cognitive analytics, CCTV motion triggers, speech-to-text lecture summarization, and an immutable SHA-256 blockchain audit ledger into a responsive, real-time web interface.

---

## Architecture Overview

```
                      +---------------------------------------+
                      |       Unified Camera Engine           |
                      | (Physical Webcams, RTSP, Synthetic)   |
                      +-------------------+-------------------+
                                          |
        +------------------+--------------+---------------+------------------+
        |                  |                              |                  |
        v                  v                              v                  v
+---------------+  +---------------+              +---------------+  +---------------+
|  Stream 1     |  |  Stream 2     |              |  Stream 3     |  |  Stream 4     |
| Face Recog &  |  | Pose Skeleton |              | Gaze Tracking |  | Threat/Weapon |
| Anti-Spoofing |  | Action Class. |              | 7 Focus Index |  | Detection     |
+-------+-------+  +-------+-------+              +-------+-------+  +-------+-------+
        |                  |                              |                  |
        +------------------+--------------+---------------+------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |     Asynchronous Event Bus            |
                      |  (Pub/Sub, Non-blocking Worker Queue) |
                      +-------------------+-------------------+
                                          |
         +--------------------------------+--------------------------------+
         |                                |                                |
         v                                v                                v
+-----------------+              +-----------------+              +-----------------+
| Notification    |              | Firebase RTDB   |              | Blockchain      |
| Engine (Siren,  |              | Service (Cloud  |              | Ledger (SHA-256 |
| Email Alerts)   |              | + Local Cache)  |              | Immutable Audit)|
+-----------------+              +-----------------+              +-----------------+
                                          |
                                          v
                      +---------------------------------------+
                      | Flask REST API & Web Dashboard Layer  |
                      | (Live MJPEG Grid, REST, Notes NLP)    |
                      +---------------------------------------+
```

---

## Key Features & AI Pipelines

### 1. Face Recognition & Anti-Spoofing Verification (Stream 1)
- **Anti-Spoofing Liveness**: Evaluates facial presentation using a custom YOLOv8 model (`models/best.pt`) classifying `real` vs `fake` faces with confidence scoring.
- **Biometric Matching**: Compares 128-dimensional facial embeddings against pre-computed identity encodings in `EncodeFile.p`.
- **Automated Attendance**: Automatically logs attendance punches, updates Firebase, and records cryptographic verification blocks.

### 2. Pose Estimation & Action/Violence Recognition (Stream 2)
- **MediaPipe Pose**: Extracts 33 anatomical landmarks across human body joints (63 normalized coordinates).
- **LSTM Action Classifier**: Temporal neural network (`ActionLSTM`) evaluating sequences of 20 consecutive frames into action classes (`neutral`, `resting`, `holding`, `gripping`, `violent`).
- **Real-Time Skeleton Visualization**: Renders color-coded joint connections and bounding boxes.

### 3. Eye Gaze Tracking & 7-Metric Concentration Analytics (Stream 3)
- **Facial Landmark Geometry**: Dlib 68-point landmark predictor tracks eye pupil centers relative to screen coordinates.
- **Blink Rate Monitoring**: Computes Eye Aspect Ratio (EAR) for continuous fatigue and attention detection.
- **7 Distinct Focus Metrics**:
  1. *Stability-Focused*: Evaluates eye fixation stability over historical frames.
  2. *Focus-Quality-Focused*: Angular alignment toward target/workstation.
  3. *Balanced Metric*: Harmonic mean of gaze stability, quality, and blink normalization.
  4. *Stability-Weighted*: Prioritizes gaze steadiness.
  5. *Focus-Weighted*: Prioritizes forward gaze orientation.
  6. *Combined-Weighted*: Balanced weighted composite.
  7. *Simple Average*: Mean arithmetic focus level.

### 4. Threat & Weapon Detection (Stream 4)
- **Custom YOLOv8 Detection**: Loaded from `runs/detect/train15/weights/best.pt`.
- **Autonomous Alarms**: Instantly activates audio sirens (`winsound` multi-frequency patterns) and dispatches background alert emails with attached snapshots.

### 5. CCTV Motion Detection & Auto-Recording
- **Background Frame Differencing**: Gaussian blur subtraction with thresholding.
- **Automated Video Capture**: Triggers `.avi` video recording upon detected motion.

### 6. Speech-to-Text & Intelligent Note Summarization
- **Audio Transcription**: Google Speech API speech-to-text with WAV/MP3 upload support.
- **NLP Heuristic Summarizer**: Cleans stop-words, calculates keyword frequencies, and extracts top sentence summaries.

### 7. Immutable Blockchain Identity & Audit Ledger
- **SHA-256 Block Chaining**: Cryptographically links all identity verifications and security alerts.
- **Zero Tampering Verification**: Automated `is_chain_valid()` audit endpoint.

---

## Project Structure

```
ProjectVision/
├── run.py                       # Main application launcher
├── requirements.txt             # Verified Python dependencies
├── core/                        # Core infrastructural engine
│   ├── config.py                # Environment and dynamic path configuration
│   ├── camera_engine.py         # Thread-safe multi-camera capture and multiplexing
│   ├── event_bus.py             # Asynchronous thread-safe pub/sub event broker
│   ├── blockchain.py            # SHA-256 tamper-evident blockchain ledger
│   └── notifications.py         # Non-blocking audio siren & email alert dispatchers
├── models/                      # AI models and inference wrappers
│   ├── face_recognizer.py       # Face recognition & anti-spoofing detector
│   ├── pose_action.py           # MediaPipe pose & ActionLSTM classifier
│   ├── gaze_tracker.py          # Dlib 68-landmark gaze & concentration analytics
│   ├── weapon_detector.py       # YOLOv8 threat and weapon detector
│   ├── motion_detector.py       # CCTV motion detection & video recorder
│   └── speech_summarizer.py     # Speech-to-text & NLP text summarizer
├── services/                    # High-level services
│   ├── pipeline_manager.py      # Multi-camera concurrent pipeline runner
│   ├── firebase_service.py      # Resilient Firebase RTDB with in-memory offline fallback
│   └── attendance_service.py    # Attendance metrics and user query manager
├── api/                         # REST API & Web Server
│   ├── routes.py                # Video feeds, REST API endpoints, web views
│   └── app.py                   # Flask application factory
├── templates/                   # HTML5 responsive web views
│   ├── dashboard.html           # Main command center dashboard
│   ├── camera_grid.html         # 4-Camera live quadrant matrix
│   ├── speech_notes.html        # Audio notes & AI summarization workspace
│   ├── blockchain_view.html     # Cryptographic blockchain explorer
│   └── students_view.html       # Student directory & attendance records
└── tests/                       # Complete automated unit & integration test suite
    ├── test_core.py             # Core engine tests
    ├── test_models.py           # AI model tests
    ├── test_pipelines.py        # Multi-camera concurrent pipeline tests
    ├── test_firebase_events.py  # Firebase & EventBus integration tests
    ├── test_api_endpoints.py    # REST API & view tests
    └── test_end_to_end.py       # Full system end-to-end integration test
```

---

## Installation & Setup

### 1. Requirements
- Python 3.10 or 3.11 (Windows, Linux, or macOS)
- Webcam (optional; engine automatically falls back to Synthetic feeds if unavailable)

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

---

## Running the Application

### Launch Command Center
```bash
python run.py
```
Options:
- `--host`: Host to bind (default: `0.0.0.0`)
- `--port`: Port to listen on (default: `5000`)
- `--verbose`: Enable debug logging
- `--no-pipelines`: Start web server without immediately initializing camera loops

### Access Web Views
Once started, open your browser:
- **Main Command Center**: [http://localhost:5000/](http://localhost:5000/)
- **4-Camera Grid View**: [http://localhost:5000/grid](http://localhost:5000/grid)
- **Audio Notes & Summarizer**: [http://localhost:5000/notes](http://localhost:5000/notes)
- **Blockchain Audit Ledger**: [http://localhost:5000/blockchain](http://localhost:5000/blockchain)
- **Student Directory**: [http://localhost:5000/students](http://localhost:5000/students)

---

## Running Automated Tests

Run the full automated test suite (36 tests):
```bash
python -m unittest discover -s tests -p "test_*.py"
```

Run specific test modules:
```bash
python -m unittest tests/test_core.py
python -m unittest tests/test_models.py
python -m unittest tests/test_pipelines.py
python -m unittest tests/test_firebase_events.py
python -m unittest tests/test_api_endpoints.py
python -m unittest tests/test_end_to_end.py
```

---

## REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/video_feed/<camera_id>` | GET | Multipart MJPEG live video stream (`cam_1` to `cam_4`, `cam_cctv`) |
| `/api/user_data` | GET | Real-time recognized student identity, profile, and attendance count |
| `/api/stats` | GET | Face recognition, real/fake classification counters |
| `/api/reset_stats` | POST | Resets anti-spoof counters |
| `/api/students` | GET | List of all registered students and attendance records |
| `/api/attendance/summary` | GET | Aggregated summary statistics |
| `/api/events` | GET | Security event log (`WEAPON_DETECTED`, `SPOOFING_DETECTED`, etc.) |
| `/api/blockchain` | GET | Full blockchain audit ledger |
| `/api/blockchain/verify` | GET | Validates SHA-256 cryptographic chain integrity |
| `/api/speech/transcribe` | POST | Transcribes uploaded audio file (`multipart/form-data`) |
| `/api/speech/summarize` | POST | Summarizes provided text (`{"text": "..."}`) |
| `/api/health` | GET | Health diagnostics for cameras, models, blockchain, and Firebase |

---

## Known Notes & Resilience Design

1. **Camera Multiplexing**: Physical webcams on Windows DirectShow cannot be opened multiple times concurrently. ProjectVision's `SharedCameraSource` captures frames from one physical descriptor and shares them across multiple AI pipelines with zero conflicts.
2. **Firebase Offline Resiliency**: If Firebase credentials expire or network is unreachable, `FirebaseService` automatically falls back to an in-memory cache populated with the baseline student registry. Attendance punches, concentration metrics, and security logs continue functioning seamlessly.
3. **Synthetic Camera Feeds**: In CI environments or headless servers where webcams are absent, the platform automatically generates procedural test frames with moving targets, timestamps, and simulated features, allowing 100% test coverage without hardware.

