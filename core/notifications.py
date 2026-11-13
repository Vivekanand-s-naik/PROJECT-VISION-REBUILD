"""
ProjectVision Asynchronous Notification Service.
Dispatches audio sirens and email alerts without blocking vision pipelines.
"""

import os
import time
import smtplib
import logging
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Optional, Any
from pathlib import Path

from core.config import config

logger = logging.getLogger("ProjectVision.Notifications")

class SoundNotifier:
    """Non-blocking sound & siren alert controller."""

    def __init__(self, cooldown_seconds: float = 5.0):
        self.cooldown = cooldown_seconds
        self._last_played: float = 0.0
        self._lock = threading.Lock()
        self._siren_running = False

    def play_alert(self, mode: str = "beep", duration: float = 1.0):
        """Play alert sound asynchronously if cooldown has elapsed."""
        if not config.SOUND_ALERTS_ENABLED:
            return

        current_time = time.time()
        with self._lock:
            if current_time - self._last_played < self.cooldown:
                return
            self._last_played = current_time

        thread = threading.Thread(target=self._play_worker, args=(mode, duration), daemon=True)
        thread.start()

    def _play_worker(self, mode: str, duration: float):
        try:
            # 1. Try winsound on Windows
            import winsound
            if mode == "siren":
                end_time = time.time() + duration
                while time.time() < end_time:
                    winsound.Beep(1200, 100)
                    winsound.Beep(1800, 100)
            elif mode == "warning":
                winsound.Beep(1500, 250)
                winsound.Beep(1000, 250)
            else:
                winsound.Beep(2000, 300)
        except Exception as e:
            logger.debug(f"Winsound not available or failed: {e}. Attempting file audio...")
            # Fallback: attempt to play audio file if playsound available
            try:
                from playsound import playsound
                sound_file = str(config.NOTIFICATION_SOUND_PATH)
                if os.path.exists(sound_file):
                    playsound(sound_file)
            except Exception:
                pass


class EmailNotifier:
    """Asynchronous SMTP email alert dispatcher with frame attachment."""

    def __init__(self, cooldown_seconds: float = 30.0):
        self.cooldown = cooldown_seconds
        self._last_sent: float = 0.0
        self._lock = threading.Lock()

    def send_alert(self, subject: str, body: str, frame: Optional[Any] = None, recipient: Optional[str] = None):
        """Send email alert in a background thread."""
        if not config.EMAIL_ALERTS_ENABLED:
            logger.debug("Email alerts are disabled in configuration.")
            return

        current_time = time.time()
        with self._lock:
            if current_time - self._last_sent < self.cooldown:
                logger.info(f"Email alert suppressed due to cooldown ({self.cooldown}s).")
                return
            self._last_sent = current_time

        thread = threading.Thread(
            target=self._send_worker,
            args=(subject, body, frame, recipient or config.ALERT_RECIPIENT_EMAIL),
            daemon=True
        )
        thread.start()

    def _send_worker(self, subject: str, body: str, frame: Optional[Any], recipient: str):
        try:
            msg = MIMEMultipart()
            msg['From'] = config.SENDER_EMAIL
            msg['To'] = recipient
            msg['Subject'] = f"[ProjectVision Alert] {subject}"

            msg.attach(MIMEText(body, 'plain'))

            if frame is not None:
                import cv2
                try:
                    if isinstance(frame, (str, Path)):
                        if os.path.exists(frame):
                            with open(frame, 'rb') as f:
                                img_data = f.read()
                            img_part = MIMEImage(img_data, name=os.path.basename(frame))
                            msg.attach(img_part)
                    else:
                        ret, buffer = cv2.imencode('.jpg', frame)
                        if ret:
                            filename = f"alert_{int(time.time())}.jpg"
                            img_part = MIMEImage(buffer.tobytes(), name=filename)
                            msg.attach(img_part)
                except Exception as img_err:
                    logger.error(f"Error attaching image to email alert: {img_err}")

            server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT, timeout=10)
            server.starttls()
            server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
            server.sendmail(config.SENDER_EMAIL, recipient, msg.as_string())
            server.quit()
            logger.info(f"Alert email successfully delivered to {recipient}")
        except Exception as e:
            logger.warning(f"Could not deliver alert email: {e}")


# Global notification instances
sound_notifier = SoundNotifier()
email_notifier = EmailNotifier()

