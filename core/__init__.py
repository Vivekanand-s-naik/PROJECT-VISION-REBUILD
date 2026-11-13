"""
ProjectVision Core Package.
Contains configuration, camera engine, asynchronous event bus, blockchain ledger, and notifications.
"""

from core.config import config
from core.camera_engine import camera_engine, BaseCameraSource, OpenCVCameraSource, SyntheticCameraSource, SharedCameraSource
from core.event_bus import event_bus, Event
from core.blockchain import identity_ledger, Blockchain, Block
from core.notifications import sound_notifier, email_notifier

__all__ = [
    "config",
    "camera_engine",
    "BaseCameraSource",
    "OpenCVCameraSource",
    "SyntheticCameraSource",
    "SharedCameraSource",
    "event_bus",
    "Event",
    "identity_ledger",
    "Blockchain",
    "Block",
    "sound_notifier",
    "email_notifier",
]

