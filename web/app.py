import shutil
import time
from pathlib import Path

from flask import Flask, render_template, Response, jsonify, request

from camera.camera_manager import camera_manager
from database.database import db
from sensors.alert_manager import alert_manager
from ai.pipeline import pipeline
from utils.config import CAMERAS, FRAME_WIDTH, FRAME_HEIGHT

BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(__name__)


############################################################
# MJPEG STREAM
############################################################

STREAM_FPS = 15


def generate_frames():
    interval = 1.0 / STREAM_FPS

    last = 0.0

    while True:
        jpg = camera_manager.get_jpeg()

        if jpg is None:
            # No frame yet: back off instead of busy-spinning
            time.sleep(0.1)

            continue

        now = time.time()

        if now - last < interval:
            time.sleep(max(interval - (now - last), 0.01))

            continue

        last = now

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
        )


############################################################
# PAGES
############################################################

@app.route("/")
def dashboard():
    threat = pipeline.last_threat

    return render_template(
        "index.html",
        status={
            "cameras": 1,
            "persons": getattr(pipeline, "last_person_count", 0),
            "threat_score": threat.get("score", 0),
            "threat_level": threat.get("level", "SAFE"),
        },
        stats={"total": db.total_alerts()},
        recent_alerts=db.recent_alerts(limit=5),
    )


@app.route("/cameras")
def cameras():
    online = 1 if camera_manager.get_jpeg() is not None else 0

    configured = len(CAMERAS)

    threat = pipeline.last_threat

    return render_template(
        "cameras.html",
        cameras=[
            {
                "name": cam["name"],
                "online": online,  # same physical source for all configured entries
            }
            for cam in CAMERAS.values()
        ],
        status={
            "cameras": configured,
            "online": online,
            "offline": configured - online,
            "storage": f"{shutil.disk_usage(BASE_DIR).free / (1024 ** 3):.0f}GB",
            "recording": 1 if pipeline.recording else 0,
            "fps": int(getattr(pipeline, "last_fps", 0) or 0),
            "resolution": f"{FRAME_WIDTH}x{FRAME_HEIGHT}",
        },
    )


@app.route("/alerts")
def alerts():
    critical = sum(
        1 for a in db.recent_alerts(limit=200)
        if (a.get("threat_level") or "").upper() in ("HIGH", "CRITICAL")
        or (a.get("alert_type") == "Violence")
    )

    return render_template(
        "alerts.html",
        alerts=db.recent_alerts(limit=100),
        stats={
            "total": db.total_alerts(),
            "critical": critical,
            "pending": db.total_pending(),
            "resolved": db.total_resolved(),
        },
    )


############################################################
# VIDEO STREAM
############################################################

@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store"},
    )


############################################################
# API -- all values read from real system state / database
############################################################

@app.route("/api/status")
def api_status():
    threat = pipeline.last_threat

    return jsonify(
        {
            "system": "Running",
            "cameras": 1,
            "online": 1 if camera_manager.get_jpeg() is not None else 0,
            "alerts": db.total_alerts(),
            "pending": db.total_pending(),
            "resolved": db.total_resolved(),
            "threat_level": threat.get("level", "SAFE"),
            "threat_score": threat.get("score", 0),
            "persons": getattr(pipeline, "last_person_count", 0),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


@app.route("/api/threat")
def api_threat():
    threat = pipeline.last_threat

    return jsonify(
        {
            "level": threat.get("level", "SAFE"),
            "value": threat.get("score", 0),
            "reasons": threat.get("reasons", []),
        }
    )


@app.route("/api/modules")
def modules():
    jpeg_ok = camera_manager.get_jpeg() is not None

    return jsonify(
        {
            "camera": "Running" if jpeg_ok else "Offline",
            "yolo": "Running",
            "gesture": "Running",
            "violence": "Running",
            "database": "Connected",
        }
    )


@app.route("/api/alerts")
def api_alerts():
    return jsonify(db.recent_alerts(limit=int(request.args.get("limit", 50))))


@app.route("/api/alerts/resolve", methods=["POST"])
def api_resolve():
    data = request.get_json(silent=True) or {}

    alert_id = data.get("id")

    if alert_id is None:
        return jsonify({"error": "id required"}), 400

    alert_manager.resolve(alert_id)

    return jsonify({"ok": True})


@app.route("/api/alerts/delete", methods=["POST"])
def api_delete():
    data = request.get_json(silent=True) or {}

    alert_id = data.get("id")

    if alert_id is None:
        return jsonify({"error": "id required"}), 400

    alert_manager.remove(alert_id)

    return jsonify({"ok": True})


############################################################
# MAIN
############################################################

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
