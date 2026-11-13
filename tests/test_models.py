"""
Unit tests for ProjectVision AI Models (Phase 4).
Tests WeaponDetector, MotionDetector, GazeTracker, FaceRecognizer,
PoseActionRecognizer, and TextSummarizer.
"""

import unittest
import numpy as np

from models.weapon_detector import WeaponDetector
from models.motion_detector import MotionDetector
from models.gaze_tracker import GazeTracker
from models.face_recognizer import FaceRecognizer
from models.pose_action import PoseActionRecognizer
from models.speech_summarizer import TextSummarizer


class TestAIModels(unittest.TestCase):

    def setUp(self):
        self.dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def test_weapon_detector(self):
        """Verify WeaponDetector runs inference without exception."""
        detector = WeaponDetector()
        ann_frame, detections = detector.detect(self.dummy_frame)
        self.assertEqual(ann_frame.shape, (480, 640, 3))
        self.assertIsInstance(detections, list)

    def test_motion_detector(self):
        """Verify MotionDetector detects motion between distinct frames."""
        md = MotionDetector(threshold=25, min_contour_area=500, auto_record_seconds=1)
        f1 = np.zeros((240, 320, 3), dtype=np.uint8)
        f2 = f1.copy()
        # Create distinct change
        f2[50:150, 50:150] = 255

        ann1, info1 = md.process_frame(f1)
        self.assertFalse(info1["motion_detected"])

        ann2, info2 = md.process_frame(f2)
        self.assertTrue(info2["motion_detected"])
        self.assertGreater(info2["motion_pixels"], 0)
        md.release()

    def test_gaze_tracker_metrics(self):
        """Verify GazeTracker 7 concentration indices calculation."""
        tracker = GazeTracker()
        metrics = tracker.generate_concentration_values(0.85, 0.75, 0.15)
        self.assertEqual(len(metrics), 7)
        for m in metrics:
            self.assertGreaterEqual(m, 0.0)
            self.assertLessEqual(m, 1.0)

        # Process frame
        ann_frame, data = tracker.process_frame(self.dummy_frame)
        self.assertIn("concentration", data)
        self.assertIn("metrics_breakdown", data)
        self.assertEqual(len(data["metrics_breakdown"]), 7)

    def test_face_recognizer(self):
        """Verify FaceRecognizer encodings loading and frame processing."""
        fr = FaceRecognizer()
        self.assertGreater(len(fr.known_ids), 0)
        self.assertIn("3", fr.known_ids)
        ann_frame, entities = fr.process_frame(self.dummy_frame)
        self.assertEqual(ann_frame.shape, (480, 640, 3))
        self.assertIsInstance(entities, list)
        stats = fr.get_stats()
        self.assertIn("total_faces_detected", stats)

    def test_pose_action_recognizer(self):
        """Verify PoseActionRecognizer sequence processing and ActionLSTM."""
        par = PoseActionRecognizer(timesteps=20)
        self.assertIsNotNone(par.model)
        ann_frame, data = par.process_frame(self.dummy_frame)
        self.assertIn("pose_detected", data)
        self.assertIn("action", data)

        # Test sequence classification with dummy buffer
        dummy_seq = [[0.0] * 63 for _ in range(20)]
        label, conf = par.classify_sequence(dummy_seq)
        self.assertIn(label, par.classes)
        self.assertGreaterEqual(conf, 0.0)

    def test_text_summarizer(self):
        """Verify TextSummarizer extraction and keyword counts."""
        ts = TextSummarizer()
        text = (
            "Computer vision enables automated biometric verification and surveillance. "
            "Deep neural networks identify weapons and violent behaviors in security video streams. "
            "Attention metrics derived from eye landmarks assist student learning."
        )
        res = ts.summarize(text)
        self.assertIn("summary", res)
        self.assertIn("keywords", res)
        self.assertGreater(len(res["keywords"]), 0)
        self.assertGreater(res["word_count"], 0)


if __name__ == "__main__":
    unittest.main()

