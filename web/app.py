from flask import Flask, render_template, Response, jsonify
import time

from camera.camera_manager import camera_manager

app = Flask(__name__)


############################################################
# MJPEG STREAM
############################################################

def generate_frames():

    while True:

        jpg = camera_manager.get_jpeg()

        if jpg is None:
            continue

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            jpg +
            b'\r\n'
        )


############################################################
# PAGES
############################################################

@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/cameras")
def cameras():
    return render_template("cameras.html")


@app.route("/alerts")
def alerts():
    return render_template("alerts.html")


############################################################
# VIDEO STREAM
############################################################

@app.route("/video_feed")
def video_feed():

    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


############################################################
# API
############################################################

@app.route("/api/status")
def api_status():

    return jsonify({

        "system": "Running",

        "cameras": 1,

        "online": 1,

        "alerts": 31,

        "threat_level": "LOW",

        "confidence": 98,

        "fps": 30,

        "latency": 22,

        "timestamp": time.strftime("%H:%M:%S")

    })


@app.route("/api/threat")
def api_threat():

    return jsonify({

        "level": "LOW",

        "value": 23

    })


@app.route("/api/modules")
def modules():

    return jsonify({

        "yolo": "Running",

        "gesture": "Running",

        "violence": "Running",

        "tracking": "Running",

        "database": "Connected"

    })


############################################################
# MAIN
############################################################

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )