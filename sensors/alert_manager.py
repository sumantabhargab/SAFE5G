import threading
import time
from datetime import datetime

from database.database import db
from utils.helpers import save_image
from utils.config import IMAGE_PATH, ALERT_COOLDOWN


class AlertManager:
    """
    Central alerting service.

    Alerts are gated by a per-type cooldown so a sustained detection
    produces one alert per ALERT_COOLDOWN seconds instead of one per frame.
    """

    def __init__(self, cooldown=ALERT_COOLDOWN):
        self.total_alerts = 0

        self.last_alert = None

        self.listeners = []

        self.cooldown = cooldown

        self._last_trigger_time = {}  # alert_type -> monotonic time

        self._lock = threading.Lock()

    def register(self, callback):
        self.listeners.append(callback)

    def notify(self, data):
        for callback in self.listeners:
            try:
                callback(data)
            except Exception as e:
                print(f"[ALERT LISTENER ERROR] {e}")

    def _should_fire(self, alert_type):
        now = time.monotonic()

        last = self._last_trigger_time.get(alert_type, 0)

        if now - last >= self.cooldown:
            self._last_trigger_time[alert_type] = now

            return True

        return False

    def play_alarm(self):
        try:
            # Imported lazily: winsound is Windows-only
            import winsound

            winsound.Beep(1500, 800)
        except Exception:
            print("[ALARM] beep unavailable on this platform")

    def trigger(
        self,
        frame,
        alert_type,
        confidence,
        camera,
        location,
        threat_level=None,
        force=False,
    ):
        """
        Fire an alert. Returns the alert dict, or None when suppressed by
        the cooldown (unless force=True).
        """
        if not force and not self._should_fire(alert_type):
            return None

        image_path = save_image(frame, IMAGE_PATH)

        alert_id = db.add_alert(
            alert_type,
            confidence,
            camera,
            location,
            image_path,
            "Pending",
        )

        with self._lock:
            self.total_alerts += 1

        alert = {
            "id": alert_id,
            "type": alert_type,
            "confidence": confidence,
            "camera": camera,
            "location": location,
            "image": image_path,
            "threat_level": threat_level,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.last_alert = alert

        threading.Thread(target=self.play_alarm, daemon=True).start()

        self.notify(alert)

        return alert

    def latest(self):
        return self.last_alert

    def count(self):
        return self.total_alerts

    def reset(self):
        self.total_alerts = 0

        self.last_alert = None

        self._last_trigger_time = {}

    def export(self):
        return db.recent_alerts()

    def history(self):
        return db.recent_alerts(limit=100)

    def statistics(self):
        return {
            "total": db.total_alerts(),
            "pending": db.total_pending(),
            "resolved": db.total_resolved(),
            "latest": self.last_alert,
        }

    def resolve(self, alert_id):
        db.update_status(alert_id, "Resolved")

    def remove(self, alert_id):
        db.delete_alert(alert_id)


alert_manager = AlertManager()
