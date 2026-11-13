"""
Unit tests for ProjectVision Core Module.
Validates Config, CameraEngine, EventBus, Blockchain, and Notifications.
"""

import time
import unittest
import numpy as np

from core.config import config
from core.camera_engine import SyntheticCameraSource, SharedCameraSource, CameraEngine
from core.event_bus import EventBus, Event
from core.blockchain import Blockchain, Block, IdentityVerificationSystem
from core.notifications import SoundNotifier, EmailNotifier

class TestCoreModules(unittest.TestCase):

    def test_config_paths(self):
        """Verify dynamic path resolution in Config."""
        self.assertTrue(config.BASE_DIR.exists())
        self.assertTrue(config.UPLOAD_FOLDER.exists())
        self.assertTrue(config.EVENTS_FOLDER.exists())
        cfg_dict = config.to_dict()
        self.assertIn("host", cfg_dict)
        self.assertIn("port", cfg_dict)
        self.assertIn("camera_sources", cfg_dict)

    def test_synthetic_camera_source(self):
        """Verify procedural synthetic camera feed produces valid BGR frames."""
        cam = SyntheticCameraSource(name="TestCam", width=320, height=240, fps=30)
        self.assertTrue(cam.is_opened())
        success, frame = cam.get_frame()
        self.assertTrue(success)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape, (240, 320, 3))
        self.assertEqual(frame.dtype, np.uint8)
        cam.release()
        self.assertFalse(cam.is_opened())

    def test_shared_camera_source(self):
        """Verify shared camera multiplexer feeds multiple consumers safely."""
        master = SyntheticCameraSource(name="Master", width=320, height=240, fps=30)
        shared_1 = SharedCameraSource(master)
        shared_2 = SharedCameraSource(master)

        s1, f1 = shared_1.get_frame()
        s2, f2 = shared_2.get_frame()

        self.assertTrue(s1)
        self.assertTrue(s2)
        self.assertEqual(f1.shape, (240, 320, 3))
        self.assertEqual(f2.shape, (240, 320, 3))
        master.release()

    def test_camera_engine_registry(self):
        """Verify CameraEngine registers feeds and handles fallback cleanly."""
        engine = CameraEngine()
        engine.register_camera("cam_1", "synthetic")
        engine.register_camera("cam_2", "shared:synthetic")

        s1, f1 = engine.get_frame("cam_1")
        s2, f2 = engine.get_frame("cam_2")

        self.assertTrue(s1)
        self.assertTrue(s2)
        self.assertIsNotNone(f1)
        self.assertIsNotNone(f2)
        engine.release_all()

    def test_event_bus_pub_sub(self):
        """Verify EventBus asynchronous pub-sub and history buffering."""
        eb = EventBus(max_history=10)
        received_events = []

        def handler(event: Event):
            received_events.append(event)

        eb.subscribe("WEAPON_DETECTED", handler)

        evt1 = Event(
            event_type="WEAPON_DETECTED",
            camera_id="cam_4",
            severity="CRITICAL",
            details={"label": "gun", "confidence": 0.95}
        )
        evt2 = Event(
            event_type="MOTION_DETECTED",
            camera_id="cam_1",
            severity="INFO",
            details={"motion_pixels": 2500}
        )

        eb.publish_sync(evt1)
        eb.publish_sync(evt2)

        # Only evt1 matches "WEAPON_DETECTED"
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].details["label"], "gun")

        # History should contain both
        history = eb.get_recent_events()
        self.assertEqual(len(history), 2)
        eb.shutdown()

    def test_blockchain_cryptographic_integrity(self):
        """Verify blockchain mining and cryptographic tamper resistance."""
        bc = Blockchain()
        self.assertEqual(len(bc.chain), 1)
        self.assertTrue(bc.is_chain_valid())

        b1 = bc.add_block({"student_id": "3", "action": "ATTENDANCE"})
        b2 = bc.add_block({"student_id": "4", "action": "ATTENDANCE"})

        self.assertEqual(len(bc.chain), 3)
        self.assertTrue(bc.is_chain_valid())

        # Test tamper detection: modify historical data
        bc.chain[1].data = {"student_id": "HACKED"}
        self.assertFalse(bc.is_chain_valid())

    def test_identity_ledger_operations(self):
        """Verify identity ledger records and lookups."""
        ledger = IdentityVerificationSystem()
        entry = ledger.record_attendance("3", "Vivekanand", status="PRESENT")
        self.assertIn("hash", entry)
        self.assertEqual(entry["data"]["student_id"], "3")

        records = ledger.get_records_by_id("3")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["data"]["student_name"], "Vivekanand")

    def test_notifications_non_blocking(self):
        """Verify sound and email dispatch without throwing or blocking."""
        s = SoundNotifier(cooldown_seconds=1.0)
        # Should execute silently / safely without crash
        s.play_alert("beep", duration=0.1)

        e = EmailNotifier(cooldown_seconds=1.0)
        # Should respect disabled email flag in test mode
        e.send_alert("Test Alert", "Testing notifier", frame=None)

if __name__ == "__main__":
    unittest.main()

