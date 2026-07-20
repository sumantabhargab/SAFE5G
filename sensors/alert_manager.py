from database.database import db
from utils.helpers import save_image
from utils.config import IMAGE_PATH
from datetime import datetime
import winsound
import threading


class AlertManager:

    def __init__(self):

        self.total_alerts = 0

        self.last_alert = None

        self.listeners = []

    def register(self, callback):

        self.listeners.append(callback)

    def notify(self, data):

        for callback in self.listeners:

            try:

                callback(data)

            except Exception as e:

                print(e)

    def play_alarm(self):

        try:

            winsound.Beep(

                1500,

                800

            )

        except:

            print("Alarm")

    def trigger(

        self,

        frame,

        alert_type,

        confidence,

        camera,

        location

    ):

        image_path = save_image(

            frame,

            IMAGE_PATH

        )

        db.add_alert(

            alert_type,

            confidence,

            camera,

            location,

            image_path,

            "Pending"

        )

        self.total_alerts += 1

        self.last_alert = {

            "type": alert_type,

            "confidence": confidence,

            "camera": camera,

            "location": location,

            "image": image_path,

            "time": datetime.now().strftime(

                "%H:%M:%S"

            )

        }

        threading.Thread(

            target=self.play_alarm,

            daemon=True

        ).start()

        self.notify(

            self.last_alert

        )

        return self.last_alert

    def latest(self):

        return self.last_alert

    def count(self):

        return self.total_alerts

    def reset(self):

        self.total_alerts = 0

        self.last_alert = None

    def export(self):

        return db.recent_alerts()

    def history(self):

        return db.recent_alerts(

            limit=100

        )

    def statistics(self):

        return {

            "total": db.total_alerts(),

            "pending": db.total_pending(),

            "resolved": db.total_resolved(),

            "latest": self.last_alert

        }

    def resolve(

        self,

        alert_id

    ):

        db.update_status(

            alert_id,

            "Resolved"

        )

    def remove(

        self,

        alert_id

    ):

        db.delete_alert(

            alert_id

        )


alert_manager = AlertManager()