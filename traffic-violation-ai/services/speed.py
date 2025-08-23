from __future__ import annotations

from typing import Dict, Tuple


class SpeedEstimator:
    def __init__(self, fps: float, meters_per_pixel: float):
        self.fps = fps
        self.meters_per_pixel = meters_per_pixel
        self.last_centroid: Dict[int, Tuple[int, int]] = {}

    def update_and_estimate_kmh(self, track_id: int, centroid: Tuple[int, int]) -> float:
        prev = self.last_centroid.get(track_id)
        self.last_centroid[track_id] = centroid
        if prev is None:
            return 0.0
        dx = centroid[0] - prev[0]
        dy = centroid[1] - prev[1]
        pixel_dist = (dx * dx + dy * dy) ** 0.5
        meters = pixel_dist * self.meters_per_pixel
        m_per_s = meters * self.fps
        kmh = m_per_s * 3.6
        return kmh

