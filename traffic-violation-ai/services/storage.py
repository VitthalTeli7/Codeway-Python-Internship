from __future__ import annotations

import os
from typing import Tuple

import cv2


def save_evidence(frame, bbox: Tuple[int, int, int, int], output_dir: str, track_id: int, frame_index: int) -> str:
    x, y, w, h = bbox
    crop = frame[max(y, 0): y + h, max(x, 0): x + w]
    os.makedirs(output_dir, exist_ok=True)
    filename = f"evidence_track{track_id}_frame{frame_index}.jpg"
    path = os.path.join(output_dir, filename)
    cv2.imwrite(path, crop)
    return path

