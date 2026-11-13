"""
ProjectVision Asynchronous Event Bus.
Decouples detection events (Spoofing, Weapons, Violence, Motion, Focus) from side effects
(Email, Sound Sirens, Firebase Sync, Blockchain Ledger, Web UI Notifications).
"""

import time
import uuid
import logging
import threading
from queue import Queue, Empty
from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("ProjectVision.EventBus")

@dataclass
class Event:
    event_type: str
    camera_id: str
    severity: str  # "INFO", "WARNING", "CRITICAL"
    details: Dict[str, Any]
    event_id: str = field(default_factory=lambda: f"evt_{int(time.time())}_{uuid.uuid4().hex[:6]}")
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    snapshot: Optional[Any] = None  # Optional numpy frame or path

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if "snapshot" in data and data["snapshot"] is not None:
            # Don't serialize raw numpy arrays into JSON dicts
            data["has_snapshot"] = True
            data.pop("snapshot", None)
        else:
            data["has_snapshot"] = False
        return data


class EventBus:
    """Thread-safe publish-subscribe event broker with background processing."""

    def __init__(self, max_history: int = 200):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._lock = threading.Lock()
        self._queue: Queue[Event] = Queue(maxsize=1000)
        self._history: List[Event] = []
        self._max_history = max_history
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True, name="EventBusWorker")
        self._worker_thread.start()
        logger.info("EventBus initialized and worker started.")

    def subscribe(self, event_type: str, handler: Callable[[Event], None]):
        """Subscribe a callable to an event type (or '*' for all events)."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler {handler.__name__ if hasattr(handler, '__name__') else handler} to {event_type}")

    def publish(self, event: Event):
        """Enqueue an event for asynchronous dispatch to subscribers."""
        if not self._running:
            return
        try:
            self._queue.put_nowait(event)
        except Exception as e:
            logger.warning(f"Event queue full, dropping event {event.event_id}: {e}")

    def publish_sync(self, event: Event):
        """Immediately dispatch event on caller thread (for testing or critical paths)."""
        self._dispatch(event)

    def _process_queue(self):
        while self._running:
            try:
                event = self._queue.get(timeout=0.5)
                self._dispatch(event)
                self._queue.task_done()
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing event in queue: {e}")

    def _dispatch(self, event: Event):
        # Record into history
        with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history.pop(0)

        # Notify specific subscribers
        handlers_to_call = []
        with self._lock:
            handlers_to_call.extend(self._subscribers.get(event.event_type, []))
            handlers_to_call.extend(self._subscribers.get("*", []))

        for handler in handlers_to_call:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Handler {handler} failed for event {event.event_id}: {e}")

    def get_recent_events(self, limit: int = 50, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            filtered = [
                e.to_dict() for e in self._history
                if event_type is None or e.event_type == event_type
            ]
            return filtered[-limit:]

    def clear_history(self):
        with self._lock:
            self._history.clear()

    def shutdown(self):
        self._running = False
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
        logger.info("EventBus shut down.")


# Global default instance
event_bus = EventBus()

