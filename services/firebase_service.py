"""
ProjectVision Resilient Firebase Realtime Database Service.
Handles student profile retrieval, attendance updates, concentration metrics sync,
and security event logging with an in-memory offline fallback cache.
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from core.config import config
from core.event_bus import event_bus, Event
from core.blockchain import identity_ledger

logger = logging.getLogger("ProjectVision.FirebaseService")


class FirebaseService:
    """Robust Firebase Realtime Database client with transparent offline fallback."""

    # Default baseline data matching repository addDatatoDatabase.py
    DEFAULT_STUDENTS = {
        "3": {
            "name": "Vivekanand",
            "major": "Computer Science & Engineering",
            "starting_year": 2023,
            "total_attendance": 10,
            "standing": "Good",
            "year": 2,
            "last_attendance_time": "2026-11-13 18:30:00",
            "concentration_data": {}
        },
        "4": {
            "name": "Sowmya Gopal",
            "major": "Computer Science & Engineering",
            "starting_year": 2023,
            "total_attendance": 10,
            "standing": "Good",
            "year": 2,
            "last_attendance_time": "2026-11-13 18:30:00",
            "concentration_data": {}
        },
        "321654": {
            "name": "Murtaza Hassan",
            "major": "Robotics & AI",
            "starting_year": 2021,
            "total_attendance": 7,
            "standing": "Good",
            "year": 4,
            "last_attendance_time": "2026-11-13 18:30:00",
            "concentration_data": {}
        },
        "852741": {
            "name": "Emily Blunt",
            "major": "Economics & Data Analytics",
            "starting_year": 2022,
            "total_attendance": 12,
            "standing": "Excellent",
            "year": 3,
            "last_attendance_time": "2026-11-13 18:30:00",
            "concentration_data": {}
        },
        "963852": {
            "name": "Elon Musk",
            "major": "Applied Physics & Systems",
            "starting_year": 2020,
            "total_attendance": 7,
            "standing": "Good",
            "year": 4,
            "last_attendance_time": "2026-11-13 18:30:00",
            "concentration_data": {}
        }
    }

    def __init__(self):
        self.firebase_initialized = False
        self.is_offline_mode = True
        self.db_ref = None
        self._local_cache: Dict[str, Dict[str, Any]] = {k: v.copy() for k, v in self.DEFAULT_STUDENTS.items()}
        self._security_events_log: List[Dict[str, Any]] = []

        self._init_firebase()
        self._setup_event_listeners()

    def _init_firebase(self):
        """Attempts to initialize official Firebase Admin SDK credentials."""
        if not config.FIREBASE_ENABLED:
            logger.info("Firebase integration is explicitly disabled in config. Using resilient local cache.")
            return

        cred_path = config.FIREBASE_CREDENTIALS_PATH
        if not cred_path.exists():
            logger.warning(f"Firebase key not found at {cred_path}. Operating in resilient offline mode.")
            return

        try:
            import firebase_admin
            from firebase_admin import credentials, db

            # Avoid re-initialization if app already exists
            if not firebase_admin._apps:
                cred = credentials.Certificate(str(cred_path))
                firebase_admin.initialize_app(cred, {
                    'databaseURL': config.FIREBASE_DB_URL
                })
            self.db_ref = db.reference()
            self.firebase_initialized = True
            self.is_offline_mode = False
            logger.info("Firebase Realtime Database initialized successfully with cloud connection.")

            # Seed remote DB if empty
            try:
                remote_students = db.reference('Students').get()
                if not remote_students:
                    logger.info("Seeding initial student records into Firebase...")
                    for s_id, s_data in self.DEFAULT_STUDENTS.items():
                        db.reference(f'Students/{s_id}').set(s_data)
                else:
                    # Update local cache with remote values
                    for s_id, s_data in remote_students.items():
                        if isinstance(s_data, dict):
                            self._local_cache[str(s_id)] = s_data
            except Exception as seed_err:
                logger.warning(f"Firebase cloud sync error during startup: {seed_err}. Falling back to local cache.")
                self.is_offline_mode = True

        except Exception as e:
            logger.warning(f"Failed to connect to Firebase cloud: {e}. Running with local in-memory fallback.")
            self.firebase_initialized = False
            self.is_offline_mode = True

    def _setup_event_listeners(self):
        """Subscribes Firebase service to real-time vision events (once)."""
        if getattr(self, "_listeners_registered", False):
            return
        self._listeners_registered = True

        event_bus.subscribe("FACE_RECOGNIZED", self._on_face_recognized)
        event_bus.subscribe("FOCUS_UPDATE", self._on_focus_update)
        event_bus.subscribe("WEAPON_DETECTED", self._on_security_event)
        event_bus.subscribe("SPOOFING_DETECTED", self._on_security_event)
        event_bus.subscribe("VIOLENCE_DETECTED", self._on_security_event)
        logger.info("Firebase event subscriptions registered.")

    def _on_face_recognized(self, event: Event):
        student_id = event.details.get("student_id")
        if student_id:
            self.update_attendance(student_id)
            # Record in blockchain ledger as well
            student = self.get_student(student_id)
            name = student.get("name", f"Student {student_id}") if student else f"Student {student_id}"
            identity_ledger.record_attendance(student_id, name, status="PRESENT", camera_id=event.camera_id)

    def _on_focus_update(self, event: Event):
        student_id = event.details.get("student_id")
        metrics = event.details.get("metrics")
        if student_id and metrics:
            self.store_concentration_metrics(student_id, metrics)

    def _on_security_event(self, event: Event):
        self.log_security_event(event.to_dict())
        # Record into immutable blockchain
        identity_ledger.record_security_event(
            event_type=event.event_type,
            camera_id=event.camera_id,
            severity=event.severity,
            details=event.details
        )

    def get_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Fetch student profile by ID."""
        student_id_str = str(student_id)
        if not self.is_offline_mode and self.db_ref:
            try:
                from firebase_admin import db
                data = db.reference(f'Students/{student_id_str}').get()
                if data:
                    self._local_cache[student_id_str] = data
                    return data
            except Exception as e:
                logger.warning(f"Firebase fetch failed for student {student_id_str}: {e}. Returning cached.")

        return self._local_cache.get(student_id_str)

    def get_all_students(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all registered student profiles."""
        if not self.is_offline_mode and self.db_ref:
            try:
                from firebase_admin import db
                remote = db.reference('Students').get()
                if remote and isinstance(remote, dict):
                    self._local_cache.update({str(k): v for k, v in remote.items() if isinstance(v, dict)})
            except Exception as e:
                logger.warning(f"Firebase get_all_students failed: {e}. Using cached.")

        return self._local_cache.copy()

    def update_attendance(self, student_id: str) -> bool:
        """Increment attendance counter and update last attendance timestamp."""
        student_id_str = str(student_id)
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update local cache first
        student = self._local_cache.get(student_id_str)
        if student is None:
            student = {
                "name": f"Student {student_id_str}",
                "major": "General",
                "starting_year": 2024,
                "total_attendance": 0,
                "standing": "Good",
                "year": 1,
                "last_attendance_time": current_time_str
            }
            self._local_cache[student_id_str] = student

        student["total_attendance"] = student.get("total_attendance", 0) + 1
        student["last_attendance_time"] = current_time_str
        logger.info(f"Attendance recorded for {student['name']} ({student_id_str}) | Total: {student['total_attendance']}")

        # Sync to cloud if online
        if not self.is_offline_mode and self.db_ref:
            try:
                from firebase_admin import db
                ref = db.reference(f'Students/{student_id_str}')
                ref.update({
                    'total_attendance': student['total_attendance'],
                    'last_attendance_time': current_time_str
                })
                return True
            except Exception as e:
                logger.warning(f"Firebase cloud attendance update failed: {e}. Kept in local cache.")

        return True

    def store_concentration_metrics(self, student_id: str, concentration_values: List[float]) -> bool:
        """Store 7-metric concentration data in student's concentration history."""
        if not concentration_values or len(concentration_values) < 7:
            return False

        student_id_str = str(student_id)
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        metrics_data = {
            'Stability-focused': round(concentration_values[0], 3),
            'Focus-quality-focused': round(concentration_values[1], 3),
            'Balanced metric': round(concentration_values[2], 3),
            'Stability-weighted': round(concentration_values[3], 3),
            'Focus-weighted': round(concentration_values[4], 3),
            'Combined-weighted': round(concentration_values[5], 3),
            'Simple average': round(concentration_values[6], 3),
            'last_update_time': timestamp_str
        }

        # Update local cache
        if student_id_str in self._local_cache:
            self._local_cache[student_id_str]['concentration_data'] = metrics_data

        # Sync to cloud
        if not self.is_offline_mode and self.db_ref:
            try:
                from firebase_admin import db
                ref = db.reference(f'Students/{student_id_str}/concentration_data')
                ref.set(metrics_data)
                return True
            except Exception as e:
                logger.warning(f"Firebase cloud metrics update failed: {e}. Cached locally.")

        return True

    def log_security_event(self, event_data: Dict[str, Any]) -> bool:
        """Append security event to Firebase and local audit log."""
        self._security_events_log.append(event_data)
        if len(self._security_events_log) > 200:
            self._security_events_log.pop(0)

        if not self.is_offline_mode and self.db_ref:
            try:
                from firebase_admin import db
                db.reference('SecurityEvents').push(event_data)
                return True
            except Exception as e:
                logger.warning(f"Failed to log security event to Firebase: {e}")

        return True

    def get_security_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._security_events_log[-limit:]

    def get_service_status(self) -> Dict[str, Any]:
        return {
            "firebase_initialized": self.firebase_initialized,
            "offline_mode": self.is_offline_mode,
            "students_cached_count": len(self._local_cache),
            "security_events_count": len(self._security_events_log)
        }


# Global Firebase service instance
firebase_service = FirebaseService()
