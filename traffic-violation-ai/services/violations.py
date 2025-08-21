from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class ViolationState:
    has_crossed_stop_line: Dict[int, bool] = field(default_factory=dict)
    still_frames_count: Dict[int, int] = field(default_factory=dict)


class ViolationRules:
    def __init__(self, stop_line_y: int, speed_limit_kmh: float, parking_min_still_seconds: int, fps: float):
        self.stop_line_y = stop_line_y
        self.speed_limit_kmh = speed_limit_kmh
        self.parking_min_still_frames = int(parking_min_still_seconds * fps)
        self.state = ViolationState()

    def check_red_light(self, track_id: int, centroid: Tuple[int, int], is_red: bool) -> bool:
        if not is_red:
            return False
        y = centroid[1]
        crossed_before = self.state.has_crossed_stop_line.get(track_id, False)
        if not crossed_before and y < self.stop_line_y:
            return False
        if not crossed_before and y >= self.stop_line_y:
            self.state.has_crossed_stop_line[track_id] = True
            return True
        return False

    def check_speeding(self, speed_kmh: float) -> bool:
        return speed_kmh > self.speed_limit_kmh

    def check_parking_or_lane(self, track_id: int, centroid: Tuple[int, int], bbox: Tuple[int, int, int, int]) -> bool:
        # Simple parking: same centroid (approximately) for N frames
        key = track_id
        count = self.state.still_frames_count.get(key, 0)
        self.state.still_frames_count[key] = count + 1
        return self.state.still_frames_count[key] > self.parking_min_still_frames

