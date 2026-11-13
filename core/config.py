"""
ProjectVision Central Configuration Module.
Dynamically resolves paths, environment settings, model locations, and thresholds.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent

@dataclass
class Config:
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "projectvision-secret-key-2026")

    # Storage paths
    BASE_DIR: Path = BASE_DIR
    UPLOAD_FOLDER: Path = BASE_DIR / "uploads"
    EVENTS_FOLDER: Path = BASE_DIR / "uploads" / "events"
    IMAGES_FOLDER: Path = BASE_DIR / "images"
    STATIC_FOLDER: Path = BASE_DIR / "static"
    TEMPLATES_FOLDER: Path = BASE_DIR / "templates"

    # Model file paths
    FACE_SPOOF_MODEL_PATH: Path = BASE_DIR / "models" / "best.pt"
    FACE_SPOOF_FALLBACK_PATH: Path = BASE_DIR / "antispoof" / "yolov8n.pt"
    WEAPON_MODEL_PATH: Path = BASE_DIR / "runs" / "detect" / "train15" / "weights" / "best.pt"
    BASE_YOLO_PATH: Path = BASE_DIR / "yolov8n.pt"
    ACTION_LSTM_MODEL_PATH: Path = BASE_DIR / "LSTM-Actions-Recognition-main" / "lstm-model.h5"
    ACTION_SUPPLEMENTARY_MODEL_PATH: Path = BASE_DIR / "LSTM-Actions-Recognition-main" / "model.h5"
    DLIB_LANDMARKS_PATH: Path = BASE_DIR / "shape_predictor_68_face_landmarks.dat"
    ENCODINGS_PATH: Path = BASE_DIR / "EncodeFile.p"

    # Audio & Assets
    NOTIFICATION_SOUND_PATH: Path = BASE_DIR / "notification.mp3"
    ALERT_SOUND_PATH: Path = BASE_DIR / "LSTM-Actions-Recognition-main" / "alert.wav"

    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH: Path = BASE_DIR / "serviceAccountKey.json"
    FIREBASE_DB_URL: str = os.getenv(
        "FIREBASE_DB_URL", "https://projectvision908-default-rtdb.firebaseio.com/"
    )
    FIREBASE_ENABLED: bool = os.getenv("FIREBASE_ENABLED", "True").lower() in ("true", "1", "yes")

    # Email Notification Settings
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "vivektemp57@gmail.com")
    SENDER_PASSWORD: str = os.getenv("SENDER_PASSWORD", "ezhw xfbz yemd dcyo")
    ALERT_RECIPIENT_EMAIL: str = os.getenv("ALERT_RECIPIENT_EMAIL", "shridharmareppagol@gmail.com")
    EMAIL_ALERTS_ENABLED: bool = os.getenv("EMAIL_ALERTS_ENABLED", "False").lower() in ("true", "1", "yes")

    # Sound Siren Settings
    SOUND_ALERTS_ENABLED: bool = os.getenv("SOUND_ALERTS_ENABLED", "True").lower() in ("true", "1", "yes")

    # Vision & Detection Thresholds
    FACE_CONFIDENCE_THRESHOLD: float = 0.60
    FACE_SIZE_THRESHOLD: int = 40000
    WEAPON_CONFIDENCE_THRESHOLD: float = 0.60
    ACTION_CONFIDENCE_THRESHOLD: float = 0.50
    BLINK_THRESHOLD: float = 0.20
    FOCUS_THRESHOLD: float = 0.70
    HISTORY_SIZE: int = 30
    UPDATE_INTERVAL_SECONDS: int = 60
    ATTENDANCE_COOLDOWN_SECONDS: int = 30

    # Camera Sources: "0" for webcam, "synthetic" for simulated feed, path to file or rtsp URL
    CAMERA_SOURCE_1: str = os.getenv("CAMERA_SOURCE_1", "0")
    CAMERA_SOURCE_2: str = os.getenv("CAMERA_SOURCE_2", "shared:0")
    CAMERA_SOURCE_3: str = os.getenv("CAMERA_SOURCE_3", "shared:0")
    CAMERA_SOURCE_4: str = os.getenv("CAMERA_SOURCE_4", "shared:0")

    def __post_init__(self):
        # Ensure directories exist
        self.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        self.EVENTS_FOLDER.mkdir(parents=True, exist_ok=True)
        self.IMAGES_FOLDER.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "host": self.HOST,
            "port": self.PORT,
            "debug": self.DEBUG,
            "firebase_enabled": self.FIREBASE_ENABLED,
            "sound_alerts_enabled": self.SOUND_ALERTS_ENABLED,
            "email_alerts_enabled": self.EMAIL_ALERTS_ENABLED,
            "face_confidence_threshold": self.FACE_CONFIDENCE_THRESHOLD,
            "weapon_confidence_threshold": self.WEAPON_CONFIDENCE_THRESHOLD,
            "camera_sources": {
                "cam_1": self.CAMERA_SOURCE_1,
                "cam_2": self.CAMERA_SOURCE_2,
                "cam_3": self.CAMERA_SOURCE_3,
                "cam_4": self.CAMERA_SOURCE_4,
            }
        }

config = Config()

