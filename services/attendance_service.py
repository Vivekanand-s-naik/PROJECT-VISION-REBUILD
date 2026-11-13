"""
ProjectVision Attendance & Student Analytics Service.
Aggregates attendance metrics, student profiles, live presence detection, and focus stats.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.firebase_service import firebase_service
from core.blockchain import identity_ledger

logger = logging.getLogger("ProjectVision.AttendanceService")


class AttendanceService:
    """Manages high-level attendance reporting and user detection queries."""

    def __init__(self):
        self.firebase = firebase_service
        self._last_detected_student: Optional[Dict[str, Any]] = None
        self._last_detected_time: float = 0.0

    def get_user_status_data(self, latest_entities: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Supplies formatted JSON payload for dashboard user card matching /get_user_data.
        """
        current_time = time.time()

        # If entities provided from recent frame
        if latest_entities and len(latest_entities) > 0:
            for entity in latest_entities:
                student_id = entity.get("id")
                if student_id:
                    student_info = self.firebase.get_student(student_id)
                    if student_info:
                        self._last_detected_student = {
                            "detected": True,
                            "id": student_id,
                            "name": student_info.get("name", "Unknown"),
                            "status": "Active / Verified",
                            "total_attendance": student_info.get("total_attendance", 0),
                            "last_attendance_time": student_info.get("last_attendance_time", "Never"),
                            "major": student_info.get("major", "N/A"),
                            "standing": student_info.get("standing", "Good"),
                            "year": student_info.get("year", 1),
                            "concentration": student_info.get("concentration_data", {})
                        }
                        self._last_detected_time = current_time
                        return self._last_detected_student

        # Check if last detected was within 10 seconds
        if self._last_detected_student and (current_time - self._last_detected_time) < 10.0:
            return self._last_detected_student

        return {
            "detected": False,
            "message": "No recognized identity in camera frame.",
            "status": "Idle / Standby"
        }

    def get_all_records(self) -> List[Dict[str, Any]]:
        """Fetch all students with attendance and focus stats."""
        students_dict = self.firebase.get_all_students()
        results = []
        for s_id, s_data in students_dict.items():
            entry = s_data.copy()
            entry["id"] = s_id
            results.append(entry)
        return results

    def get_attendance_summary(self) -> Dict[str, Any]:
        """Summary dashboard counters."""
        all_students = self.get_all_records()
        total_registered = len(all_students)
        active_today = sum(1 for s in all_students if s.get("total_attendance", 0) > 0)
        total_punches = sum(s.get("total_attendance", 0) for s in all_students)

        return {
            "total_registered_students": total_registered,
            "active_today": active_today,
            "total_attendance_punches": total_punches,
            "blockchain_blocks_count": len(identity_ledger.get_ledger()),
            "last_sync": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# Global attendance service
attendance_service = AttendanceService()

