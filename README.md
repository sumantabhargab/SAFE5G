# 

# Safe5G

AI-based Women Safety Surveillance System using Computer Vision and Deep Learning.

---

# Features

- Real-time CCTV Monitoring
- YOLOv8 Object Detection
- Naruto SOS Hand Gesture Detection
- Violence Detection
- Crowd Detection
- Vehicle Detection
- Emergency Alert Generation
- Incident Recording
- Dashboard Monitoring
- SQLite Database
- Automatic Report Generation

---

# Folder Structure

Safe5G/

├── ai/

├── camera/

├── database/

├── media/

├── models/

├── rules/

├── sensors/

├── utils/

├── web/

├── requirements.txt

├── run.py

└── README.md

---

# Installation

Clone repository

```bash
git clone https://github.com/yourusername/Safe5G.git
```

Go inside project

```bash
cd Safe5G
```

Create Virtual Environment

Windows

```bash
python -m venv venv
```

Activate

```bash
venv\Scripts\activate
```

Linux

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Download Models

YOLO

Download

```
yolov8n.pt
```

Place inside

```
models/
```

Gesture Model

```
gesture.onnx
```

Violence Model

```
violence.keras
```

---

# Run

```bash
python run.py
```

Dashboard

```
http://127.0.0.1:5000
```

---

# AI Pipeline

Camera

↓

YOLO Detection

↓

Gesture Detection

↓

Violence Detection

↓

Rule Engine

↓

Alert Manager

↓

SOS Trigger

↓

Database

↓

Dashboard

---

# Database

SQLite

Tables

- Alerts
- Logs

---

# Generated Media

Images

```
media/images
```

Videos

```
media/videos
```

Reports

```
media/reports
```

---

# Reports

Automatically generates

- TXT
- CSV
- JSON

---

# Technologies

Python

OpenCV

YOLOv8

TensorFlow

MediaPipe

Flask

SQLite

NumPy

Pandas

---

# Future Scope

Live CCTV

Face Recognition

Weapon Detection

Fire Detection

Smoke Detection

GPS Tracking

Drone Surveillance

Cloud Dashboard

Android App

5G Edge Deployment

Police Integration

Emergency Call API

---

# Author

Sumanta Bhargab

Safe5G

IEEE CMES Research Project