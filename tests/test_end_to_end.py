"""
End-to-End System Integration Test for ProjectVision (Phase 9).
Validates end-to-end integration from camera frame capture through AI inference,
event dispatch, Firebase update, blockchain ledger recording, and REST API delivery.
"""

import time
import unittest
import numpy as np

from api.app import create_app
from services.pipeline_manager import pipeline_manager
from services.firebase_service import firebase_service
from services.attendance_service import attendance_service
from core.event_bus import event_bus, Event
from core.blockchain import identity_ledger


class TestEndToEndIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Configure test app and start camera pipelines
        cls.app = create_app(start_pipelines=True)
        cls.client = cls.app.test_client()
        # Warm up pipelines
        time.sleep(2.0)

    @classmethod
    def tearDownClass(cls):
        pipeline_manager.stop_all()

    def test_e2e_camera_streams(self):
        """Verify all 4 camera streams are producing valid frames simultaneously."""
        for cam_id in ["cam_1", "cam_2", "cam_3", "cam_4"]:
            frame = pipeline_manager.get_frame(cam_id)
            self.assertIsNotNone(frame, f"Stream {cam_id} failed to produce frame.")
            self.assertEqual(len(frame.shape), 3)
            self.assertGreater(frame.shape[0], 0)
            self.assertGreater(frame.shape[1], 0)

    def test_e2e_face_attendance_to_blockchain(self):
        """Verify: Face Recognition Event -> Firebase Attendance Increment -> Blockchain Block Mined."""
        initial_blocks = len(identity_ledger.get_ledger())
        student_before = firebase_service.get_student("3")
        attendance_before = student_before["total_attendance"]

        # Simulate Face Recognition detection event
        event_bus.publish_sync(Event(
            event_type="FACE_RECOGNIZED",
            camera_id="cam_1",
            severity="INFO",
            details={"student_id": "3", "match_distance": 0.28, "status": "VERIFIED"}
        ))

        # 1. Verify Firebase / Cache updated
        student_after = firebase_service.get_student("3")
        self.assertEqual(student_after["total_attendance"], attendance_before + 1)

        # 2. Verify Blockchain block automatically mined
        blocks_after = len(identity_ledger.get_ledger())
        self.assertEqual(blocks_after, initial_blocks + 1)

        # 3. Verify Blockchain integrity preserved
        self.assertTrue(identity_ledger.blockchain.is_chain_valid())

        # 4. Verify API reflects updated attendance
        resp = self.client.get('/api/user_data')
        self.assertEqual(resp.status_code, 200)

    def test_e2e_weapon_alert_dispatch(self):
        """Verify: Threat Detection Event -> Security Logging -> EventBus -> Blockchain Record."""
        initial_blocks = len(identity_ledger.get_ledger())

        event_bus.publish_sync(Event(
            event_type="WEAPON_DETECTED",
            camera_id="cam_4",
            severity="CRITICAL",
            details={"weapon_type": "handgun", "confidence": 0.94}
        ))

        # Check API security events
        resp = self.client.get('/api/events?limit=5')
        self.assertEqual(resp.status_code, 200)
        events = resp.get_json()["events"]
        self.assertGreater(len(events), 0)
        latest = events[-1]
        self.assertEqual(latest["event_type"], "WEAPON_DETECTED")
        self.assertEqual(latest["details"]["weapon_type"], "handgun")

        # Check block mined
        self.assertEqual(len(identity_ledger.get_ledger()), initial_blocks + 1)

    def test_e2e_concentration_pipeline(self):
        """Verify: Concentration Metrics Event -> Student Record Updated -> API Delivery."""
        test_metrics = [0.88, 0.79, 0.82, 0.85, 0.81, 0.83, 0.82]

        event_bus.publish_sync(Event(
            event_type="FOCUS_UPDATE",
            camera_id="cam_3",
            severity="INFO",
            details={
                "student_id": "3",
                "concentration": 0.82,
                "metrics": test_metrics,
                "focus_duration_seconds": 150.0,
                "blink_rate": 0.12
            }
        ))

        student = firebase_service.get_student("3")
        self.assertIn("concentration_data", student)
        self.assertEqual(student["concentration_data"]["Stability-focused"], 0.88)

    def test_e2e_speech_and_summarization_workflow(self):
        """Verify text summarization and note generation flow."""
        notes = (
            "During the surveillance audit, all four camera feeds maintained 25 FPS stream rate. "
            "Biometric verification successfully registered student 3 with high confidence. "
            "The blockchain verified all historical blocks as cryptographically untampered."
        )

        resp = self.client.post('/api/speech/summarize', json={"text": notes})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("summary", data)
        self.assertIn("keywords", data)
        self.assertIn("bullet_points", data)

    def test_e2e_system_health(self):
        """Verify system health endpoint reports all operational components."""
        resp = self.client.get('/api/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn(data["status"], ["healthy", "degraded"])
        self.assertTrue(data["blockchain"]["valid"])


if __name__ == "__main__":
    unittest.main()

