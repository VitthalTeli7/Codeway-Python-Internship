Traffic Violation Detection (Computer Vision + Deep Learning)
=============================================================

Overview
--------
Detect vehicles, track them, and identify violations:
- Red light jumping
- Over-speeding
- Illegal parking / lane violation
- License plate recognition (OCR)
- Automatic fine generation and database logging

Tech Stack
---------
- Python 3.9+
- OpenCV
- YOLOv5/YOLOv8 (optional) or classical motion + centroid tracker (default)
- DeepSORT / ByteTrack (optional)
- EasyOCR / Tesseract (optional)
- SQLite (default) or MySQL
- Flask dashboard

Quick Start
----------
```bash
cd traffic-violation-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run CLI on a sample video
python -m app.main --input sample.mp4 --output-dir static/evidence

# Run dashboard
FLASK_APP=app.main flask run --reload
```

Zip Download
------------
If you received this as a source tree, you can zip it yourself:
```bash
cd ..
zip -r traffic-violation-ai.zip traffic-violation-ai
```

Features in this scaffold
-------------------------
- Minimal vehicle detection via background subtraction (no heavy weights bundled)
- Centroid-based tracking
- Speed estimation via pixel distance/time and calibration factor
- Red light zone crossing rule
- OCR integration hooks (stubbed if Tesseract not installed)
- Evidence snapshot saving and SQLite logging
- Simple Flask dashboard to view violations

Configuration
-------------
See `config/config.yaml` for thresholds, ROI, speed calibration, and DB path.

Project Layout
--------------
```
app/
  __init__.py
  main.py              # CLI + Flask
models/
  __init__.py
  db.py                # SQLite models and queries
services/
  detector.py          # Background subtraction detector (pluggable)
  tracker.py           # Centroid tracker
  speed.py             # Speed estimation
  violations.py        # Rule engine
  ocr.py               # OCR integration (optional)
  storage.py           # Evidence saving
config/config.yaml
templates/
  index.html           # Dashboard
static/
  evidence/            # Saved snapshots
  css/
requirements.txt
README.md
```

Notes
-----
- Replace the simple detector with a YOLO model for production.
- Provide camera FPS and pixel-to-meter calibration for accurate speeds.
- Tesseract requires system install (apt-get) if you enable OCR.

License
-------
MIT
