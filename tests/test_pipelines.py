"""
Unit and integration tests for Multi-Camera Pipeline Processing (Phase 5).
Verifies concurrent pipeline execution, MJPEG streaming, thread safety, and lifecycle management.
"""

import time
import unittest
from services.pipeline_manager import PipelineManager


class TestMultiCameraPipeline(unittest.TestCase):

    def setUp(self):
        self.pm = PipelineManager()
        self.pm.initialize()

    def tearDown(self):
        self.pm.stop_all()

    def test_pipeline_workers_registration(self):
        """Verify all 5 pipelines are correctly registered."""
        self.assertIn("cam_1", self.pm.workers)
        self.assertIn("cam_2", self.pm.workers)
        self.assertIn("cam_3", self.pm.workers)
        self.assertIn("cam_4", self.pm.workers)
        self.assertIn("cam_cctv", self.pm.workers)

    def test_concurrent_pipeline_execution(self):
        """Verify pipelines run concurrently and acquire frames without crashing."""
        self.pm.start_all()

        # Let pipelines process frames across concurrent threads
        time.sleep(1.5)

        statuses = self.pm.get_all_statuses()
        for cam_id in ["cam_1", "cam_2", "cam_3", "cam_4", "cam_cctv"]:
            self.assertIn(cam_id, statuses)
            self.assertTrue(statuses[cam_id]["running"])

        # Fetch frame from cam_1
        f1 = self.pm.get_frame("cam_1")
        self.assertIsNotNone(f1)
        self.assertEqual(len(f1.shape), 3)

    def test_mjpeg_stream_generation(self):
        """Verify MJPEG generator yields multipart HTTP JPEG boundaries."""
        self.pm.start_all()
        time.sleep(0.5)

        stream = self.pm.generate_mjpeg_stream("cam_1")
        chunk = next(stream)
        self.assertIsInstance(chunk, bytes)
        self.assertIn(b"--frame", chunk)
        self.assertIn(b"Content-Type: image/jpeg", chunk)


if __name__ == "__main__":
    unittest.main()

