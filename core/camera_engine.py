"""
ProjectVision Unified Camera & Video Streaming Engine.
Provides thread-safe frame acquisition, camera multiplexing, and support for:
- Physical Webcams (cv2.VideoCapture(0, 1...))
- Video Files (.mp4, .avi)
- RTSP / HTTP IP Camera Streams
- Shared Camera Feeds (multiplexing single webcam across multiple AI pipelines)
- Synthetic Test Feeds (for automated testing and headless environments)
"""

import time
import math
import logging
import threading
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Optional, Any
import numpy as np
import cv2

from core.config import config

logger = logging.getLogger("ProjectVision.CameraEngine")


class BaseCameraSource(ABC):
    """Abstract base class for all camera stream providers."""

    @abstractmethod
    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Return (success, frame_bgr)."""
        pass

    @abstractmethod
    def is_opened(self) -> bool:
        """Return True if source is operational."""
        pass

    @abstractmethod
    def release(self):
        """Release underlying hardware or network resources."""
        pass


class OpenCVCameraSource(BaseCameraSource):
    """Physical webcam, video file, or RTSP/HTTP network stream."""

    def __init__(self, source_uri: Any, width: int = 640, height: int = 480, target_fps: int = 30):
        self.source_uri = source_uri
        self.width = width
        self.height = height
        self.target_fps = target_fps
        self._delay = 1.0 / target_fps
        self._last_frame_time = 0.0
        self._lock = threading.Lock()
        self.cap: Optional[cv2.VideoCapture] = None
        self._init_capture()

    def _init_capture(self):
        try:
            # Parse integer index if numeric string
            if isinstance(self.source_uri, str) and self.source_uri.isdigit():
                source = int(self.source_uri)
            else:
                source = self.source_uri

            self.cap = cv2.VideoCapture(source)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                logger.info(f"OpenCV capture initialized for {self.source_uri}")
            else:
                logger.warning(f"Failed to open OpenCV capture for {self.source_uri}")
        except Exception as e:
            logger.error(f"Error opening camera source {self.source_uri}: {e}")
            self.cap = None

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        with self._lock:
            if self.cap is None or not self.cap.isOpened():
                return False, None

            ret, frame = self.cap.read()
            if not ret or frame is None:
                # If video file reached the end, loop back to start
                if isinstance(self.source_uri, str) and not self.source_uri.isdigit():
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()

                if not ret or frame is None:
                    return False, None

            # Resize if needed
            if frame.shape[1] != self.width or frame.shape[0] != self.height:
                frame = cv2.resize(frame, (self.width, self.height))

            # Pace frame acquisition
            now = time.time()
            elapsed = now - self._last_frame_time
            if elapsed < self._delay:
                time.sleep(self._delay - elapsed)
            self._last_frame_time = time.time()

            return True, frame

    def is_opened(self) -> bool:
        with self._lock:
            return self.cap is not None and self.cap.isOpened()

    def release(self):
        with self._lock:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
                logger.info(f"Released OpenCV camera source {self.source_uri}")


class SyntheticCameraSource(BaseCameraSource):
    """
    Simulated camera feed that produces high-quality procedural test frames.
    Renders moving target shapes, mock faces, timestamps, and camera stats.
    Essential for headless CI/CD, unit tests, and systems without webcams.
    """

    def __init__(self, name: str = "SyntheticCam", width: int = 640, height: int = 480, fps: int = 30):
        self.name = name
        self.width = width
        self.height = height
        self.fps = fps
        self._delay = 1.0 / fps
        self._start_time = time.time()
        self._frame_count = 0
        self._opened = True
        self._lock = threading.Lock()

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        with self._lock:
            if not self._opened:
                return False, None

            self._frame_count += 1
            t = time.time() - self._start_time

            # Create dark gradient background
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            # Add subtle grid lines
            for y in range(0, self.height, 40):
                cv2.line(frame, (0, y), (self.width, y), (25, 25, 30), 1)
            for x in range(0, self.width, 40):
                cv2.line(frame, (x, 0), (x, self.height), (25, 25, 30), 1)

            # Draw simulated moving subject (mock face / target)
            center_x = int(self.width / 2 + math.sin(t * 1.5) * 120)
            center_y = int(self.height / 2 + math.cos(t * 1.0) * 60)

            # Simulated face circle and features
            cv2.circle(frame, (center_x, center_y), 55, (200, 180, 140), -1)
            cv2.circle(frame, (center_x, center_y), 55, (100, 200, 100), 2)
            # Eyes
            cv2.circle(frame, (center_x - 18, center_y - 12), 6, (40, 40, 40), -1)
            cv2.circle(frame, (center_x + 18, center_y - 12), 6, (40, 40, 40), -1)
            # Mouth
            cv2.ellipse(frame, (center_x, center_y + 18), (18, 8), 0, 0, 180, (40, 40, 180), 2)

            # Frame headers and timestamps
            timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, f"{self.name} [LIVE VIRTUAL FEED]", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 128), 2)
            cv2.putText(frame, f"Time: {timestamp_str} | Frame: {self._frame_count}", (15, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            cv2.putText(frame, f"FPS: {self.fps} | Res: {self.width}x{self.height}", (15, self.height - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

            # Pulsing status indicator
            pulse_color = (0, int(150 + 105 * math.sin(t * 4)), 0)
            cv2.circle(frame, (self.width - 25, 25), 8, pulse_color, -1)

            time.sleep(self._delay)
            return True, frame

    def is_opened(self) -> bool:
        return self._opened

    def release(self):
        with self._lock:
            self._opened = False


class SharedCameraSource(BaseCameraSource):
    """
    Multiplexer for a single master camera source.
    Multiple pipeline consumers request frames from SharedCameraSource without
    opening conflicting OS camera descriptors.
    """

    def __init__(self, master_source: BaseCameraSource):
        self.master = master_source
        self._lock = threading.Lock()
        self._cached_frame: Optional[np.ndarray] = None
        self._last_fetch_time: float = 0.0
        self._cache_lifetime: float = 0.015  # 15 ms cache for 60fps sharing

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        now = time.time()
        with self._lock:
            if self._cached_frame is not None and (now - self._last_fetch_time) < self._cache_lifetime:
                return True, self._cached_frame.copy()

            success, frame = self.master.get_frame()
            if success and frame is not None:
                self._cached_frame = frame
                self._last_fetch_time = now
                return True, frame.copy()
            elif self._cached_frame is not None:
                # Return last known frame if master had a momentary glitch
                return True, self._cached_frame.copy()
            return False, None

    def is_opened(self) -> bool:
        return self.master.is_opened()

    def release(self):
        # Do not release the shared master from child subscriber
        pass


class CameraEngine:
    """Central camera registry and manager."""

    def __init__(self):
        self._sources: Dict[str, BaseCameraSource] = {}
        self._shared_masters: Dict[str, BaseCameraSource] = {}
        self._lock = threading.Lock()
        self._auto_fallback_to_synthetic = True

    def initialize_cameras(self):
        """Initialize camera feeds based on global configuration."""
        camera_configs = {
            "cam_1": config.CAMERA_SOURCE_1,
            "cam_2": config.CAMERA_SOURCE_2,
            "cam_3": config.CAMERA_SOURCE_3,
            "cam_4": config.CAMERA_SOURCE_4,
        }

        for cam_id, source_spec in camera_configs.items():
            self.register_camera(cam_id, source_spec)

    def register_camera(self, cam_id: str, source_spec: str):
        """Create and register a camera source."""
        with self._lock:
            # Release existing if registered
            if cam_id in self._sources:
                self._sources[cam_id].release()

            source = self._create_source(cam_id, source_spec)
            self._sources[cam_id] = source
            logger.info(f"Registered camera '{cam_id}' with source type '{source_spec}'")

    def _create_source(self, cam_id: str, spec: str) -> BaseCameraSource:
        spec_clean = spec.strip().lower()

        # Synthetic explicitly requested
        if spec_clean == "synthetic" or spec_clean.startswith("mock"):
            return SyntheticCameraSource(name=f"Camera-{cam_id.upper()}")

        # Shared camera spec (e.g. "shared:0" or "shared:cam_1")
        if spec_clean.startswith("shared:"):
            target_key = spec_clean.split(":", 1)[1]
            if target_key not in self._shared_masters:
                # Create master source
                if target_key.isdigit():
                    master = OpenCVCameraSource(int(target_key))
                    if not master.is_opened() and self._auto_fallback_to_synthetic:
                        logger.warning(f"Hardware camera {target_key} unavailable, falling back to Synthetic.")
                        master = SyntheticCameraSource(name=f"SharedMaster-{target_key}")
                else:
                    master = SyntheticCameraSource(name=f"SharedMaster-{target_key}")
                self._shared_masters[target_key] = master

            return SharedCameraSource(self._shared_masters[target_key])

        # Physical hardware camera or file
        if spec_clean.isdigit():
            cam_idx = int(spec_clean)
            opencv_source = OpenCVCameraSource(cam_idx)
            if not opencv_source.is_opened():
                if self._auto_fallback_to_synthetic:
                    logger.warning(f"Webcam index {cam_idx} not found on system. Falling back to Synthetic source.")
                    return SyntheticCameraSource(name=f"Camera-{cam_id.upper()}")
            return opencv_source

        # RTSP, HTTP, or video file path
        opencv_source = OpenCVCameraSource(spec)
        if not opencv_source.is_opened() and self._auto_fallback_to_synthetic:
            logger.warning(f"Video stream {spec} could not be opened. Falling back to Synthetic source.")
            return SyntheticCameraSource(name=f"Camera-{cam_id.upper()}")
        return opencv_source

    def get_frame(self, cam_id: str) -> Tuple[bool, Optional[np.ndarray]]:
        with self._lock:
            source = self._sources.get(cam_id)
            if source is None:
                return False, None
            return source.get_frame()

    def get_source(self, cam_id: str) -> Optional[BaseCameraSource]:
        with self._lock:
            return self._sources.get(cam_id)

    def release_all(self):
        with self._lock:
            for source in self._sources.values():
                try:
                    source.release()
                except Exception as e:
                    logger.error(f"Error releasing camera: {e}")
            self._sources.clear()

            for master in self._shared_masters.values():
                try:
                    master.release()
                except Exception as e:
                    logger.error(f"Error releasing shared master: {e}")
            self._shared_masters.clear()
            logger.info("All camera sources released.")


# Global camera engine instance
camera_engine = CameraEngine()

