from pathlib import Path
from datetime import datetime
import csv
import json

from database.database import db
from utils.config import REPORT_PATH


class ReportGenerator:

    def __init__(self):

        REPORT_PATH.mkdir(

            parents=True,

            exist_ok=True

        )

    def timestamp(self):

        return datetime.now().strftime(

            "%Y%m%d_%H%M%S"

        )

    def text_report(self):

        alerts = db.recent_alerts(

            limit=1000

        )

        file = REPORT_PATH / f"report_{self.timestamp()}.txt"

        with open(

            file,

            "w",

            encoding="utf-8"

        ) as f:

            f.write(

                "SAFE5G INCIDENT REPORT\n"

            )

            f.write(

                "=" * 60 + "\n\n"

            )

            for alert in alerts:

                f.write(

                    f"ID : {alert['id']}\n"

                )

                f.write(

                    f"Type : {alert['alert_type']}\n"

                )

                f.write(

                    f"Confidence : {alert['confidence']}\n"

                )

                f.write(

                    f"Camera : {alert['camera']}\n"

                )

                f.write(

                    f"Location : {alert['location']}\n"

                )

                f.write(

                    f"Status : {alert['status']}\n"

                )

                f.write(

                    f"Time : {alert['created_at']}\n"

                )

                f.write(

                    "-" * 60 + "\n"

                )

        return str(file)

    def csv_report(self):

        alerts = db.recent_alerts(

            limit=1000

        )

        file = REPORT_PATH / f"report_{self.timestamp()}.csv"

        with open(

            file,

            "w",

            newline="",

            encoding="utf-8"

        ) as csvfile:

            writer = csv.writer(

                csvfile

            )

            writer.writerow([

                "ID",

                "Type",

                "Confidence",

                "Camera",

                "Location",

                "Image",

                "Status",

                "Created"

            ])

            for alert in alerts:

                writer.writerow([

                    alert["id"],

                    alert["alert_type"],

                    alert["confidence"],

                    alert["camera"],

                    alert["location"],

                    alert["image"],

                    alert["status"],

                    alert["created_at"]

                ])

        return str(file)

    def json_report(self):

        alerts = db.recent_alerts(

            limit=1000

        )

        file = REPORT_PATH / f"report_{self.timestamp()}.json"

        with open(

            file,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                alerts,

                f,

                indent=4

            )

        return str(file)

    def summary(self):

        return {

            "total_alerts": db.total_alerts(),

            "pending": db.total_pending(),

            "resolved": db.total_resolved()

        }

    def generate_all(self):

        return {

            "text": self.text_report(),

            "csv": self.csv_report(),

            "json": self.json_report(),

            "summary": self.summary()

        }


report_generator = ReportGenerator()