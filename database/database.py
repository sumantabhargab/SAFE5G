import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from utils.config import DATABASE


class Database:
    """
    Thread-safe SQLite wrapper.

    A single connection guarded by a lock is safe here because every
    operation is short; WAL mode lets readers proceed while a write commits.
    """

    def __init__(self, db_path=DATABASE):
        self.db_path = Path(db_path)

        self._lock = threading.Lock()

        self.connection = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
        )

        self.connection.row_factory = sqlite3.Row

        self.connection.execute("PRAGMA journal_mode=WAL")

        self.connection.execute("PRAGMA busy_timeout=5000")

        self.create_tables()

    def create_tables(self):
        with self._lock:
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS alerts(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT,
                    confidence REAL,
                    camera TEXT,
                    location TEXT,
                    image TEXT,
                    threat_level TEXT,
                    status TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS logs(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    module TEXT,
                    message TEXT,
                    level TEXT,
                    timestamp TEXT
                );
                """
            )

            self.connection.commit()

    def add_alert(
        self,
        alert_type,
        confidence,
        camera,
        location,
        image="",
        threat_level=None,
        status="Pending",
    ):
        with self._lock:
            cursor = self.connection.execute(
                """
                INSERT INTO alerts(
                    alert_type,
                    confidence,
                    camera,
                    location,
                    image,
                    threat_level,
                    status,
                    created_at
                )
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    alert_type,
                    confidence,
                    camera,
                    location,
                    image,
                    threat_level,
                    status,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

            self.connection.commit()

            return cursor.lastrowid

    def add_log(self, module, message, level="INFO"):
        with self._lock:
            self.connection.execute(
                """
                INSERT INTO logs(
                    module,
                    message,
                    level,
                    timestamp
                )
                VALUES(?,?,?,?)
                """,
                (
                    module,
                    message,
                    level,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

            self.connection.commit()

    def recent_alerts(self, limit=20):
        with self._lock:
            rows = self.connection.execute(
                """
                SELECT *
                FROM alerts
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    def all_logs(self, limit=500):
        with self._lock:
            rows = self.connection.execute(
                """
                SELECT *
                FROM logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    def update_status(self, alert_id, status):
        with self._lock:
            self.connection.execute(
                """
                UPDATE alerts
                SET status=?
                WHERE id=?
                """,
                (status, alert_id),
            )

            self.connection.commit()

    def delete_alert(self, alert_id):
        with self._lock:
            self.connection.execute(
                "DELETE FROM alerts WHERE id=?",
                (alert_id,),
            )

            self.connection.commit()

    def total_alerts(self):
        with self._lock:
            row = self.connection.execute("SELECT COUNT(*) FROM alerts").fetchone()

        return row[0]

    def total_pending(self):
        with self._lock:
            row = self.connection.execute(
                "SELECT COUNT(*) FROM alerts WHERE status='Pending'"
            ).fetchone()

        return row[0]

    def total_resolved(self):
        with self._lock:
            row = self.connection.execute(
                "SELECT COUNT(*) FROM alerts WHERE status='Resolved'"
            ).fetchone()

        return row[0]

    def close(self):
        with self._lock:
            self.connection.close()


db = Database()
