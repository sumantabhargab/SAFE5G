import os
import base64
import threading

import requests

from sensors.alert_manager import alert_manager


class SOSTrigger:
    """
    Emergency escalation service.

    Channels:
    - webhook: real HTTP POST (with status check and one retry) when
      SOS_WEBHOOK is configured via .env or configure().
    - sms / email: adapters intended for Twilio / SMTP. They are stubs that
      log clearly; they never pretend to have sent anything.
    """

    def __init__(self):
        self.phone_number = os.getenv("SOS_PHONE", "")

        self.email = os.getenv("SOS_EMAIL", "")

        self.webhook = os.getenv("SOS_WEBHOOK", "")

        self.enabled = True

    def configure(self, phone="", email="", webhook=""):
        self.phone_number = phone

        self.email = email

        self.webhook = webhook

    def send_sms(self, message):
        # Integrate Twilio/Fast2SMS here (needs credentials + number)
        print(f"[SMS - NOT CONFIGURED] {message}")

    def send_email(self, subject, body):
        # Integrate SMTP here (needs credentials + recipient)
        print(f"[EMAIL - NOT CONFIGURED] {subject}")

    def send_webhook(self, payload):
        if not self.webhook:
            print("[WEBHOOK - NOT CONFIGURED] set SOS_WEBHOOK to enable")

            return

        for attempt in (1, 2):
            try:
                response = requests.post(
                    self.webhook,
                    json=payload,
                    timeout=5,
                )

                if response.status_code < 400:
                    print(f"[WEBHOOK] delivered (status {response.status_code})")

                    return

                print(f"[WEBHOOK] attempt {attempt} failed: HTTP {response.status_code}")
            except Exception as e:
                print(f"[WEBHOOK] attempt {attempt} error: {e}")

    def _payload(self, alert, frame=None):
        payload = dict(alert)

        # Attach the snapshot inline so remote receivers can use it
        if frame is not None:
            try:
                import cv2

                ok, buf = cv2.imencode(".jpg", frame)

                if ok:
                    payload["image_base64"] = base64.b64encode(buf).decode("ascii")
            except Exception as e:
                print(f"[WEBHOOK] snapshot encode failed: {e}")

        return payload

    def activate(self, alert, frame=None):
        if not self.enabled:
            return

        message = (
            f"Emergency Alert\n"
            f"Type : {alert['type']}\n"
            f"Camera : {alert['camera']}\n"
            f"Location : {alert['location']}\n"
            f"Time : {alert['time']}"
        )

        payload = self._payload(alert, frame)

        threading.Thread(target=self.send_sms, args=(message,), daemon=True).start()

        threading.Thread(
            target=self.send_email,
            args=("Safe5G Emergency", message),
            daemon=True,
        ).start()

        threading.Thread(
            target=self.send_webhook,
            args=(payload,),
            daemon=True,
        ).start()

    def help_detected(self, frame, confidence, camera, location, threat_level=None):
        alert = alert_manager.trigger(
            frame,
            "HELP Gesture",
            confidence,
            camera,
            location,
            threat_level=threat_level,
        )

        if alert is None:
            return None

        self.activate(alert, frame)

        return alert

    def violence_detected(self, frame, confidence, camera, location, threat_level=None):
        alert = alert_manager.trigger(
            frame,
            "Violence",
            confidence,
            camera,
            location,
            threat_level=threat_level,
        )

        if alert is None:
            return None

        self.activate(alert, frame)

        return alert

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True


sos_trigger = SOSTrigger()
