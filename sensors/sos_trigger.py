import threading
import requests
from datetime import datetime

from sensors.alert_manager import alert_manager


class SOSTrigger:

    def __init__(self):

        self.phone_number = ""

        self.email = ""

        self.webhook = ""

        self.enabled = True

    def configure(

        self,

        phone="",

        email="",

        webhook=""

    ):

        self.phone_number = phone

        self.email = email

        self.webhook = webhook

    def send_sms(self, message):

        print(

            f"[SMS] {message}"

        )

        # Integrate Twilio/Fast2SMS here

    def send_email(

        self,

        subject,

        body

    ):

        print(

            f"[EMAIL] {subject}"

        )

        # Integrate SMTP here

    def send_webhook(

        self,

        payload

    ):

        if not self.webhook:

            return

        try:

            requests.post(

                self.webhook,

                json=payload,

                timeout=5

            )

        except Exception as e:

            print(e)

    def activate(

        self,

        alert,

        frame=None

    ):

        if not self.enabled:

            return

        message = (

            f"Emergency Alert\n"

            f"Type : {alert['type']}\n"

            f"Camera : {alert['camera']}\n"

            f"Location : {alert['location']}\n"

            f"Time : {alert['time']}"

        )

        threading.Thread(

            target=self.send_sms,

            args=(message,),

            daemon=True

        ).start()

        threading.Thread(

            target=self.send_email,

            args=(

                "Safe5G Emergency",

                message

            ),

            daemon=True

        ).start()

        threading.Thread(

            target=self.send_webhook,

            args=(alert,),

            daemon=True

        ).start()

    def help_detected(

        self,

        frame,

        confidence,

        camera,

        location

    ):

        alert = alert_manager.trigger(

            frame,

            "HELP Gesture",

            confidence,

            camera,

            location

        )

        self.activate(

            alert,

            frame

        )

    def violence_detected(

        self,

        frame,

        confidence,

        camera,

        location

    ):

        alert = alert_manager.trigger(

            frame,

            "Violence",

            confidence,

            camera,

            location

        )

        self.activate(

            alert,

            frame

        )

    def disable(self):

        self.enabled = False

    def enable(self):

        self.enabled = True


sos_trigger = SOSTrigger()