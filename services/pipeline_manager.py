"""
ProjectVision Multi-Camera Pipeline Orchestrator.
Manages concurrent AI vision pipelines across multiple cameras:
- Pipeline 1: Face Recognition & Anti-Spoofing (cam_1)
- Pipeline 2: Pose Estimation & Action/Violence Recognition (cam_2)
- Pipeline 3: Gaze Tracking & Concentration Analytics (cam_3)
- Pipeline 4: Weapon & Threat Detection (cam_4)
- Optional CCTV Motion Detection Pipeline (cam_cctv)
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, Generator
import cv2
import numpy as np

from core.config import config
from core.camera_engine import camera_engine
from core.event_bus import event_bus, Event
from models.face_recognizer import FaceRecognizer
from models.pose_action import PoseActionRecognizer
from models.gaze_tracker import GazeTracker
from models.weapon_detector import WeaponDetector
from models.motion_detector import MotionDetector

logger = logging.getLogger("ProjectVision.PipelineManager")


class CameraPipelineWorker:
    """Manages an individual camera's AI processing loop in a dedicated thread."""

    def __init__(self,
                 camera_id: str,
                 pipeline_type: str,
                 processor: Any,
                 target_fps: int = 25):
        self.camera_id = camera_id
        self.pipeline_type = pipeline_type
        self.processor = processor
        self.target_fps = target_fps
        self._delay = 1.0 / target_fps

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._latest_output_frame: Optional[np.ndarray] = None
        self._latest_metadata: Dict[str, Any] = {}
        self._frame_count: int = 0
        self._fps_actual: float = 0.0
        self._last_fps_calc_time = time.time()
        self._fps_counter = 0

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True

        # If an existing thread is still winding down, wait cleanly
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name=f"Worker-{self.camera_id}-{self.pipeline_type}"
        )
        self._thread.start()
        logger.info(f"Started pipeline worker for {self.camera_id} [{self.pipeline_type}]")

    def signal_stop(self):
        with self._lock:
            self._running = False

    def wait_stopped(self, timeout: float = 0.5):
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        self._thread = None
        with self._lock:
            self._latest_output_frame = None

    def stop(self):
        self.signal_stop()
        self.wait_stopped()
        logger.info(f"Stopped pipeline worker for {self.camera_id}")

    def _run_loop(self):
        while self._running:
            loop_start = time.time()

            # 1. Fetch raw frame from CameraEngine
            success, raw_frame = camera_engine.get_frame(self.camera_id)
            if not success or raw_frame is None:
                time.sleep(0.04)
                continue

            # 2. Process frame with specialized AI model
            try:
                annotated_frame = raw_frame
                metadata = {}

                if self.pipeline_type == "face_recognition":
                    annotated_frame, entities = self.processor.process_frame(raw_frame, camera_id=self.camera_id)
                    metadata = {"entities": entities, "stats": self.processor.get_stats()}

                elif self.pipeline_type == "pose_action":
                    annotated_frame, metadata = self.processor.process_frame(raw_frame, camera_id=self.camera_id)

                elif self.pipeline_type == "gaze_tracking":
                    annotated_frame, metadata = self.processor.process_frame(raw_frame, camera_id=self.camera_id)

                elif self.pipeline_type == "weapon_detection":
                    annotated_frame, detections = self.processor.detect(raw_frame, camera_id=self.camera_id)
                    metadata = {"detections": detections}

                elif self.pipeline_type == "motion_detection":
                    annotated_frame, metadata = self.processor.process_frame(raw_frame, camera_id=self.camera_id)

                else:
                    annotated_frame = raw_frame

                # Store latest annotated frame safely
                with self._lock:
                    self._latest_output_frame = annotated_frame
                    self._latest_metadata = metadata
                    self._frame_count += 1
                    self._fps_counter += 1

                # Calculate actual FPS periodically
                now = time.time()
                if now - self._last_fps_calc_time >= 1.0:
                    with self._lock:
                        self._fps_actual = round(self._fps_counter / (now - self._last_fps_calc_time), 1)
                        self._fps_counter = 0
                        self._last_fps_calc_time = now

            except Exception as e:
                logger.error(f"Error in pipeline {self.pipeline_type} for {self.camera_id}: {e}")

            # 3. Throttle loop to target FPS
            elapsed = time.time() - loop_start
            if elapsed < self._delay:
                time.sleep(self._delay - elapsed)

    def get_latest_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            if self._latest_output_frame is not None:
                return self._latest_output_frame.copy()
        # Warm-up fallback: return live camera frame if model is still warming up
        success, raw_frame = camera_engine.get_frame(self.camera_id)
        if success and raw_frame is not None:
            return raw_frame.copy()
        return None

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "camera_id": self.camera_id,
                "pipeline_type": self.pipeline_type,
                "running": self._running,
                "frame_count": self._frame_count,
                "fps": self._fps_actual,
                "metadata": self._latest_metadata
            }


class PipelineManager:
    """Orchestrates all concurrent camera workers and MJPEG streaming."""

    def __init__(self):
        self.workers: Dict[str, CameraPipelineWorker] = {}
        self._lock = threading.Lock()
        self._initialized = False
        self._system_active = False

    @property
    def is_active(self) -> bool:
        return self._system_active

    def initialize(self):
        """Builds all AI models and registers the default 4-camera pipeline."""
        with self._lock:
            if self._initialized:
                return

            logger.info("Initializing ProjectVision Multi-Camera Pipelines...")
            camera_engine.initialize_cameras()

            # Instantiate model processors
            face_recognizer = FaceRecognizer()
            pose_recognizer = PoseActionRecognizer()
            gaze_tracker = GazeTracker()
            weapon_detector = WeaponDetector()
            motion_detector = MotionDetector()

            # Register workers
            self.workers["cam_1"] = CameraPipelineWorker("cam_1", "face_recognition", face_recognizer)
            self.workers["cam_2"] = CameraPipelineWorker("cam_2", "pose_action", pose_recognizer)
            self.workers["cam_3"] = CameraPipelineWorker("cam_3", "gaze_tracking", gaze_tracker)
            self.workers["cam_4"] = CameraPipelineWorker("cam_4", "weapon_detection", weapon_detector)
            self.workers["cam_cctv"] = CameraPipelineWorker("cam_1", "motion_detection", motion_detector)

            self._initialized = True
            logger.info("All pipeline workers registered.")

    def start_all(self):
        """Start all registered camera processing threads."""
        self.initialize()
        # Ensure camera engine has active camera sources initialized
        camera_engine.initialize_cameras()
        with self._lock:
            for worker in self.workers.values():
                worker.start()
            self._system_active = True
        logger.info("All camera pipeline workers started. Vision system is ACTIVE.")

    def stop_all(self):
        """Stop all camera processing threads and release resources."""
        with self._lock:
            # Signal stop to all workers concurrently
            for worker in self.workers.values():
                worker.signal_stop()
            # Wait for threads to terminate with short timeout
            for worker in self.workers.values():
                worker.wait_stopped(timeout=0.3)
            camera_engine.release_all()
            self._system_active = False
        logger.info("All camera pipeline workers stopped. Vision system is in STANDBY.")

    def get_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Fetch the latest processed frame from a camera worker."""
        if not self._system_active:
            return None
        worker = self.workers.get(camera_id)
        if worker is not None:
            return worker.get_latest_frame()
        return None

    def get_all_statuses(self) -> Dict[str, Any]:
        """Return diagnostic metrics and active stats for all cameras."""
        statuses = {}
        with self._lock:
            for cam_id, worker in self.workers.items():
                statuses[cam_id] = worker.get_status()
        return statuses

    def _create_standby_frame(self, camera_id: str) -> np.ndarray:
        """Generates a styled offline/standby frame when cameras are not running."""
        frame = np.full((480, 640, 3), (25, 23, 15), dtype=np.uint8)  # Deep slate #0f172a
        # Decorative border
        cv2.rectangle(frame, (8, 8), (632, 472), (45, 40, 30), 1)
        cv2.rectangle(frame, (10, 10), (630, 470), (55, 50, 40), 1)

        # Center card
        cv2.rectangle(frame, (110, 130), (530, 350), (35, 30, 22), -1)
        cv2.rectangle(frame, (110, 130), (530, 350), (70, 60, 45), 1)

        cam_names = {
            "cam_1": "CAM 01: ENTRANCE (ATTENDANCE)",
            "cam_2": "CAM 02: HALLWAY (POSE & ACTION)",
            "cam_3": "CAM 03: WORKSTATION (GAZE & FOCUS)",
            "cam_4": "CAM 04: PERIMETER (THREAT & WEAPON)",
            "cam_cctv": "CAM CCTV: MOTION DETECTOR"
        }
        cam_title = cam_names.get(camera_id, camera_id.upper())

        cv2.putText(frame, cam_title, (135, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 2)
        cv2.putText(frame, "SYSTEM STANDBY - CAMERAS INACTIVE", (135, 225), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 180, 255), 2)
        cv2.putText(frame, "Click 'Start System' button in dashboard to activate feed", (135, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1)
        cv2.putText(frame, "Role-Based Gating: Admin or Faculty Authorization Required", (135, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (120, 120, 120), 1)

        # Bottom HUD bar
        cv2.putText(frame, f"STATUS: STANDBY | STREAM: {camera_id.upper()} | {time.strftime('%H:%M:%S')}", (20, 455), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1)
        return frame

    def generate_mjpeg_stream(self, camera_id: str) -> Generator[bytes, None, None]:
        """
        Yields multipart MJPEG HTTP stream frames for browser <img src="..."> tags.
        """
        while True:
            try:
                if not self._system_active:
                    frame = self._create_standby_frame(camera_id)
                else:
                    frame = self.get_frame(camera_id)
                    if frame is None:
                        # Warm-up fallback: read raw frame directly from camera engine
                        success, raw = camera_engine.get_frame(camera_id)
                        if success and raw is not None:
                            frame = raw
                        else:
                            frame = self._create_standby_frame(camera_id)

                ret, jpeg_buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    frame_bytes = jpeg_buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
            except GeneratorExit:
                break
            except Exception as e:
                logger.error(f"Error encoding MJPEG frame for {camera_id}: {e}")

            time.sleep(0.04)  # 25 FPS stream rate


# Global PipelineManager instance
pipeline_manager = PipelineManager()
