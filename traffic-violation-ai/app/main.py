from __future__ import annotations

import argparse
import os
from typing import List

import yaml
from flask import Flask, render_template, send_from_directory

from models.db import create_session, log_violation, Violation
from services.detector import SimpleMotionDetector
from services.tracker import CentroidTracker
from services.speed import SpeedEstimator
from services.violations import ViolationRules
from services.storage import save_evidence

import cv2


def load_config():
    with open(os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml"), "r") as f:
        return yaml.safe_load(f)


def process_video(input_path: str, output_dir: str, db_uri: str, cfg):
    cap = cv2.VideoCapture(input_path)
    fps = cfg["video"].get("fps", 30)
    m_per_px = cfg["video"].get("speed_calibration_m_per_pixel", 0.05)
    stop_line_y = cfg["video"].get("stop_line_y", 300)
    speed_limit = cfg["violations"].get("speed_limit_kmh", 60)
    parking_still_secs = cfg["violations"].get("parking_min_still_seconds", 60)

    detector = SimpleMotionDetector()
    tracker = CentroidTracker(max_lost=30)
    speed = SpeedEstimator(fps=fps, meters_per_pixel=m_per_px)
    rules = ViolationRules(stop_line_y, speed_limit, parking_still_secs, fps)
    session = create_session(db_uri)

    frame_index = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        detections = detector.detect(frame)
        bboxes = [d.bbox for d in detections]
        tracks = tracker.update(bboxes, frame_index)

        # Simulate red signal always red for demo; replace with signal state
        is_red = True

        for tr in tracks:
            kmh = speed.update_and_estimate_kmh(tr.track_id, tr.centroid)
            red_light = rules.check_red_light(tr.track_id, tr.centroid, is_red)
            speeding = rules.check_speeding(kmh)
            parking = False  # disable by default to avoid noise in demo

            if red_light or speeding or parking:
                evidence_path = save_evidence(frame, tr.bbox, output_dir, tr.track_id, frame_index)
                vtype = "Red Light Jump" if red_light else ("Over Speeding" if speeding else "Parking/Lane Violation")
                log_violation(session, violation_type=vtype, vehicle_no=None, speed_kmh=kmh if speeding else None, location=None, evidence_path=evidence_path)

        frame_index += 1

    cap.release()


def create_app():
    cfg = load_config()
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"), static_folder=os.path.join(os.path.dirname(__file__), "..", "static"))
    session = create_session(cfg["database"]["uri"])

    @app.route("/")
    def index():
        violations: List[Violation] = session.query(Violation).order_by(Violation.timestamp.desc()).limit(200).all()
        return render_template("index.html", violations=violations)

    @app.route("/evidence/<path:filename>")
    def evidence(filename: str):
        return send_from_directory(os.path.join(app.static_folder, "evidence"), filename)

    return app


def main():
    parser = argparse.ArgumentParser(description="Traffic Violation Detection")
    parser.add_argument("--input", required=False, help="Path to input video", default=None)
    parser.add_argument("--output-dir", required=False, default=os.path.join(os.path.dirname(__file__), "..", "static", "evidence"))
    parser.add_argument("--run-dashboard", action="store_true")
    args = parser.parse_args()

    cfg = load_config()

    if args.input:
        process_video(args.input, args.output_dir, cfg["database"]["uri"], cfg)

    if args.run_dashboard:
        app = create_app()
        app.run(host=cfg["dashboard"]["host"], port=cfg["dashboard"]["port"], debug=True)


if __name__ == "__main__":
    main()

