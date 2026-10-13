import shutil
import threading
import time
import uuid
from pathlib import Path

import cv2
from flask import Flask, render_template, Response, jsonify, request, redirect, url_for, send_from_directory

from camera.camera_manager import camera_manager
from database.database import db
from sensors.alert_manager import alert_manager
from ai.pipeline import pipeline
from ai.gesture_detector import gesture_detector
from ai.violence_detector import violence_detector
from ai.yolo_detector import yolo_detector
from utils.config import CAMERAS, FRAME_WIDTH, FRAME_HEIGHT, MEDIA_DIR

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
            "track_ids": getattr(pipeline, "last_track_ids", []),
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
            "yolo": "Running" if yolo_detector.ready else "Error",
            "gesture": "Running" if gesture_detector.ready else "Error",
            "violence": "Running" if violence_detector.ready else "Error",
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
# VIDEO UPLOAD & ANALYSIS
############################################################

UPLOAD_FOLDER = MEDIA_DIR / "uploads"
ANALYSIS_FOLDER = MEDIA_DIR / "analysis"
ANALYSIS_OUTPUT_FOLDER = MEDIA_DIR / "analysis_output"

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ANALYSIS_FOLDER.mkdir(parents=True, exist_ok=True)
ANALYSIS_OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "flv", "wmv"}

# Thread-safe analysis result cache
_analysis_cache = {}
_analysis_lock = threading.Lock()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def process_video(video_path):
    """
    Process a video file through YOLO + violence classifier pipeline.
    Returns (timeline_events, summary_dict).
    Also writes an annotated output video.
    """
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Downscale for faster processing — cap at 480px wide
    target_w = 480
    if width > target_w:
        scale = target_w / width
    else:
        scale = 1.0

    out_fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_video_path = str(ANALYSIS_OUTPUT_FOLDER / f"{Path(video_path).stem}_output.mp4")
    writer = cv2.VideoWriter(
        out_video_path,
        out_fourcc,
        max(int(fps), 1),
        (int(width * scale), int(height * scale)),
    )

    timeline = []
    summary_events = {
        "violence": 0, "help_gesture": 0,
        "total_frames_processed": 0, "max_violence_score": 0.0,
        "avg_person_count": 0, "person_sum": 0,
    }
    frames_in_event = 0
    current_event_type = None
    event_start_time = 0.0
    person_count_accumulator = 0

    frame_idx = 0

    # Reset detectors for a clean analysis run.
    # The upload thread creates its own IMAGE-mode gesture landmarker so it
    # does not conflict with the live camera loop's VIDEO-mode instance.
    violence_detector.reset()
    import mediapipe as mp
    from mediapipe.tasks.python import vision
    from utils.config import GESTURE_CONFIRM_FRAMES, MODEL_DIR
    from ai.gesture_detector import GestureDetector

    _up_lm = None
    _gesture_last = False

    def _detect_gesture_img(frame):
        nonlocal _up_lm
        if _up_lm is None:
            model_path = MODEL_DIR / "hand_landmarker.task"
            opts = vision.HandLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
                running_mode=vision.RunningMode.IMAGE,
                num_hands=2,
                min_hand_detection_confidence=0.6,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            _up_lm = vision.HandLandmarker.create_from_options(opts)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
        )

        results = _up_lm.detect(mp_image)

        palm_this_frame = False
        lm_list = []

        if results.hand_landmarks:
            for hand_landmarks, hand_info in zip(
                results.hand_landmarks, results.handedness,
            ):
                label = hand_info[0].category_name
                # Open-palm check
                wrist = hand_landmarks[0]
                fingers_up = 0
                for tip_idx, pip_idx in [(8,6),(12,10),(16,14),(20,18)]:
                    tip = hand_landmarks[tip_idx]
                    pip = hand_landmarks[pip_idx]
                    d_tip = (tip.x-wrist.x)**2 + (tip.y-wrist.y)**2
                    d_pip = (pip.x-wrist.x)**2 + (pip.y-wrist.y)**2
                    if d_tip > d_pip * 1.1:
                        fingers_up += 1
                # Thumb
                if label == "Left":
                    thumb_ext = hand_landmarks[4].x < hand_landmarks[3].x
                else:
                    thumb_ext = hand_landmarks[4].x > hand_landmarks[3].x
                thumb_span = abs(hand_landmarks[4].x - hand_landmarks[5].x) > abs(hand_landmarks[3].x - hand_landmarks[5].x)
                if fingers_up == 4 and thumb_ext and thumb_span:
                    palm_this_frame = True
                for p in hand_landmarks:
                    lm_list.append((p.x, p.y))

        # Temporal confirmation
        if not hasattr(_detect_gesture_img, "_confirm"):
            _detect_gesture_img._confirm = 0
        if palm_this_frame:
            _detect_gesture_img._confirm += 1
        else:
            _detect_gesture_img._confirm = 0
        help_detected = _detect_gesture_img._confirm >= GESTURE_CONFIRM_FRAMES

        annotated = frame.copy()
        if help_detected:
            cv2.putText(annotated, "HELP GESTURE DETECTED", (20,70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 3)

        return {
            "help": help_detected,
            "hands": len(results.hand_landmarks) if results.hand_landmarks else 0,
            "landmarks": lm_list,
            "frame": annotated,
        }

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            if scale != 1.0:
                frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)

            frame_h, frame_w = frame.shape[:2]

            # YOLO + violence every frame (required for accurate sliding window)
            yolo_result = yolo_detector.detect(frame)
            person_count = yolo_result["person_count"]
            output = yolo_result["frame"]

            violence_result = violence_detector.detect(output)
            violence_detected = violence_result["violence"]
            violence_score = violence_result["score"]

            # Gesture detection: every 3rd frame (hands change slowly, temporal
            # confirmation smooths the gaps; GESTURE_CONFIRM_FRAMES=5 means we
            # need 5 frames of palm — skipping every 3rd → 15 wall frames = 0.5s
            if frame_idx % 3 == 0:
                gesture_result = _detect_gesture_img(output)
                help_detected = gesture_result["help"]
                _gesture_last = help_detected  # persist in closure scope
            else:
                help_detected = _gesture_last
                gesture_result = {"help": help_detected, "hands": 0, "landmarks": [], "frame": output}

            person_count_accumulator += person_count
            summary_events["total_frames_processed"] += 1

            if violence_score > summary_events["max_violence_score"]:
                summary_events["max_violence_score"] = violence_score

            # Violence events (coalesce consecutive violent frames)
            if violence_detected:
                summary_events["violence"] += 1
                if current_event_type is None:
                    current_event_type = "violence"
                    event_start_time = frame_idx / fps
                frames_in_event += 1
            else:
                if current_event_type == "violence" and frames_in_event > 0:
                    timeline.append({
                        "type": "violence",
                        "start": round(event_start_time, 2),
                        "end": round((frame_idx - frames_in_event) / fps, 2),
                        "duration": round(frames_in_event / fps, 2),
                        "confidence": round(summary_events["max_violence_score"], 3),
                    })
                    current_event_type = None
                    frames_in_event = 0

            # HELP gesture events
            if help_detected:
                summary_events["help_gesture"] += 1
                if current_event_type is None:
                    current_event_type = "help_gesture"
                    event_start_time = frame_idx / fps
                frames_in_event += 1
            elif current_event_type == "help_gesture" and frames_in_event > 0:
                timeline.append({
                    "type": "help_gesture",
                    "start": round(event_start_time, 2),
                    "end": round((frame_idx - frames_in_event) / fps, 2),
                    "duration": round(frames_in_event / fps, 2),
                    "confidence": 0.9,
                })
                current_event_type = None
                frames_in_event = 0

            # Annotated overlay
            if violence_detected:
                cv2.rectangle(output, (0, 0), (frame_w, 60), (0, 0, 255), -1)
                cv2.putText(output, "VIOLENCE DETECTED", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            if help_detected:
                cv2.rectangle(output, (0, 0), (frame_w, 60), (255, 165, 0), -1)
                cv2.putText(output, "HELP GESTURE DETECTED", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            cv2.putText(output, f"Persons: {person_count}", (20, frame_h - 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(output, f"Violence: {violence_score:.2f}", (20, frame_h - 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 0, 255) if violence_detected else (0, 255, 0), 2)
            cv2.putText(output, f"{frame_idx}/{total_frames}", (frame_w - 120, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            writer.write(output)
            frame_idx += 1

    finally:
        cap.release()
        writer.release()

    # Flush open events at video end
    if current_event_type == "violence" and frames_in_event > 0:
        timeline.append({
            "type": "violence",
            "start": round(event_start_time, 2),
            "end": round(frame_idx / fps, 2),
            "duration": round(frames_in_event / fps, 2),
            "confidence": round(summary_events["max_violence_score"], 3),
        })
    elif current_event_type == "help_gesture" and frames_in_event > 0:
        timeline.append({
            "type": "help_gesture",
            "start": round(event_start_time, 2),
            "end": round(frame_idx / fps, 2),
            "duration": round(frames_in_event / fps, 2),
            "confidence": 0.9,
        })

    avg_persons = (person_count_accumulator / summary_events["total_frames_processed"]
                   if summary_events["total_frames_processed"] > 0 else 0)
    summary_events["avg_person_count"] = round(avg_persons, 1)
    summary_events["video_duration"] = round(frame_idx / fps, 2)
    summary_events["total_frames"] = frame_idx
    summary_events["fps"] = round(fps, 1)

    return timeline, summary_events


@app.route("/upload", methods=["GET"])
def upload_page():
    return render_template("upload.html")


@app.route("/upload", methods=["POST"])
def upload_video():
    video_file = request.files.get("video")

    if not video_file or not allowed_file(video_file.filename):
        return jsonify({"error": "Allowed formats: mp4, avi, mov, mkv, flv, wmv"}), 400

    video_id = uuid.uuid4().hex[:12]
    ext = video_file.filename.rsplit(".", 1)[1].lower()
    video_path = UPLOAD_FOLDER / f"{video_id}.{ext}"

    video_file.save(str(video_path))

    # Start async analysis in background thread
    with _analysis_lock:
        _analysis_cache[video_id] = {"status": "processing", "results": None, "ext": ext}

    def run_analysis():
        try:
            results, summary = process_video(str(video_path))
            with _analysis_lock:
                _analysis_cache[video_id] = {
                    "status": "done",
                    "results": results,
                    "summary": summary,
                    "ext": ext,
                }
        except Exception as e:
            with _analysis_lock:
                _analysis_cache[video_id] = {
                    "status": "error",
                    "error": str(e),
                    "ext": ext,
                }

    threading.Thread(target=run_analysis, daemon=True).start()

    return jsonify({
        "video_id": video_id,
        "ext": ext,
    })


@app.route("/api/video/status/<video_id>", methods=["GET"])
def video_status(video_id):
    with _analysis_lock:
        entry = _analysis_cache.get(video_id)

    if not entry or entry["status"] == "processing":
        return jsonify({"status": "pending"}), 202

    if entry["status"] == "error":
        return jsonify({"status": "error", "error": entry["error"]}), 500

    return jsonify({
        "status": "done",
        "results": entry["results"],
        "summary": entry["summary"],
        "video_path": url_for("static_analysis_output", filename=f"{video_id}_output.mp4"),
    })


############################################################
# STATIC FILES (uploaded videos + output videos)
############################################################

@app.route("/static/uploads/<path:filename>")
def static_uploads(filename):
    return send_from_directory(str(UPLOAD_FOLDER), filename)


@app.route("/static/analysis_output/<path:filename>")
def static_analysis_output(filename):
    return send_from_directory(str(ANALYSIS_OUTPUT_FOLDER), filename)


############################################################
# MAIN
############################################################

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
