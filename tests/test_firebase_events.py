"""
Unit and integration tests for Event Management & Firebase Integration (Phase 6).
Tests FirebaseService, EventBus automatic listeners, and AttendanceService.
"""

import unittest
from core.event_bus import event_bus, Event
from core.blockchain import identity_ledger
from services.firebase_service import firebase_service
from services.attendance_service import attendance_service


class TestFirebaseAndEvents(unittest.TestCase):

    def setUp(self):
        self.fb = firebase_service
        self.att = attendance_service

    def test_get_student_profile(self):
        """Verify student retrieval from cache/Firebase."""
        student = self.fb.get_student("3")
        self.assertIsNotNone(student)
        self.assertEqual(student["name"], "Vivekanand")

    def test_update_attendance(self):
        """Verify attendance counter increments correctly."""
        initial = self.fb.get_student("3")["total_attendance"]
        self.fb.update_attendance("3")
        updated = self.fb.get_student("3")["total_attendance"]
        self.assertEqual(updated, initial + 1)

    def test_store_concentration_metrics(self):
        """Verify all 7 concentration metrics are persisted."""
        metrics = [0.82, 0.74, 0.78, 0.80, 0.76, 0.77, 0.78]
        success = self.fb.store_concentration_metrics("3", metrics)
        self.assertTrue(success)
        student = self.fb.get_student("3")
        self.assertIn("concentration_data", student)
        c_data = student["concentration_data"]
        self.assertIn("Balanced metric", c_data)
        self.assertEqual(c_data["Balanced metric"], 0.78)

    def test_event_bus_automatic_firebase_sync(self):
        """Verify publishing events on EventBus automatically triggers Firebase & Blockchain."""
        initial_blocks = len(identity_ledger.get_ledger())

        # Publish security event
        event_bus.publish_sync(Event(
            event_type="WEAPON_DETECTED",
            camera_id="cam_4",
            severity="CRITICAL",
            details={"weapon_type": "knife", "confidence": 0.88}
        ))

        # Check that event was logged in Firebase service
        recent_events = self.fb.get_security_events(limit=5)
        self.assertGreater(len(recent_events), 0)
        self.assertEqual(recent_events[-1]["details"]["weapon_type"], "knife")

        # Check that blockchain block was automatically added (single increment)
        new_blocks = len(identity_ledger.get_ledger())
        self.assertEqual(new_blocks, initial_blocks + 1)

    def test_attendance_service_summary(self):
        """Verify attendance summary counter aggregation."""
        summary = self.att.get_attendance_summary()
        self.assertIn("total_registered_students", summary)
        self.assertGreater(summary["total_registered_students"], 0)
        self.assertIn("blockchain_blocks_count", summary)


if __name__ == "__main__":
    unittest.main()
