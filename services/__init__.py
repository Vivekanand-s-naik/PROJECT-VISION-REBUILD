"""
ProjectVision Services Package.
Contains:
- pipeline_manager: Multi-camera concurrent pipeline runner
- firebase_service: Real-time DB cloud sync & local offline cache
- attendance_service: Student profile and attendance metrics management
"""

from services.pipeline_manager import pipeline_manager, PipelineManager
from services.firebase_service import firebase_service, FirebaseService
from services.attendance_service import attendance_service, AttendanceService

__all__ = [
    "pipeline_manager",
    "PipelineManager",
    "firebase_service",
    "FirebaseService",
    "attendance_service",
    "AttendanceService",
]

