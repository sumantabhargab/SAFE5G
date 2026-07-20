import sqlite3
from pathlib import Path
from datetime import datetime


DATABASE = Path("safe5g.db")


class Database:

    def __init__(self):

        self.connection = sqlite3.connect(

            DATABASE,

            check_same_thread=False

        )

        self.connection.row_factory = sqlite3.Row

        self.cursor = self.connection.cursor()

        self.create_tables()

    def create_tables(self):

        self.cursor.execute("""

        CREATE TABLE IF NOT EXISTS alerts(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            alert_type TEXT,

            confidence REAL,

            camera TEXT,

            location TEXT,

            image TEXT,

            status TEXT,

            created_at TEXT

        )

        """)

        self.cursor.execute("""

        CREATE TABLE IF NOT EXISTS logs(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            module TEXT,

            message TEXT,

            level TEXT,

            timestamp TEXT

        )

        """)

        self.connection.commit()

    def add_alert(

        self,

        alert_type,

        confidence,

        camera,

        location,

        image="",

        status="Pending"

    ):

        self.cursor.execute("""

        INSERT INTO alerts(

            alert_type,

            confidence,

            camera,

            location,

            image,

            status,

            created_at

        )

        VALUES(?,?,?,?,?,?,?)

        """, (

            alert_type,

            confidence,

            camera,

            location,

            image,

            status,

            datetime.now().strftime(

                "%Y-%m-%d %H:%M:%S"

            )

        ))

        self.connection.commit()

    def add_log(

        self,

        module,

        message,

        level="INFO"

    ):

        self.cursor.execute("""

        INSERT INTO logs(

            module,

            message,

            level,

            timestamp

        )

        VALUES(?,?,?,?)

        """, (

            module,

            message,

            level,

            datetime.now().strftime(

                "%Y-%m-%d %H:%M:%S"

            )

        ))

        self.connection.commit()

    def recent_alerts(self, limit=20):

        self.cursor.execute("""

        SELECT *

        FROM alerts

        ORDER BY id DESC

        LIMIT ?

        """, (limit,))

        return [

            dict(row)

            for row in self.cursor.fetchall()

        ]

    def all_logs(self):

        self.cursor.execute("""

        SELECT *

        FROM logs

        ORDER BY id DESC

        """)

        return [

            dict(row)

            for row in self.cursor.fetchall()

        ]

    def update_status(

        self,

        alert_id,

        status

    ):

        self.cursor.execute("""

        UPDATE alerts

        SET status=?

        WHERE id=?

        """, (

            status,

            alert_id

        ))

        self.connection.commit()

    def delete_alert(self, alert_id):

        self.cursor.execute(

            "DELETE FROM alerts WHERE id=?",

            (alert_id,)

        )

        self.connection.commit()

    def total_alerts(self):

        self.cursor.execute(

            "SELECT COUNT(*) FROM alerts"

        )

        return self.cursor.fetchone()[0]

    def total_pending(self):

        self.cursor.execute("""

        SELECT COUNT(*)

        FROM alerts

        WHERE status='Pending'

        """)

        return self.cursor.fetchone()[0]

    def total_resolved(self):

        self.cursor.execute("""

        SELECT COUNT(*)

        FROM alerts

        WHERE status='Resolved'

        """)

        return self.cursor.fetchone()[0]

    def close(self):

        self.connection.close()


db = Database()