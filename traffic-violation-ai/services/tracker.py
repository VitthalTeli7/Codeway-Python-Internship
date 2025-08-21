from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np


@dataclass
class Track:
    track_id: int
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    centroid: Tuple[int, int]
    last_seen_frame: int


class CentroidTracker:
    def __init__(self, max_lost: int = 30):
        self.next_id = 1
        self.tracks: Dict[int, Track] = {}
        self.max_lost = max_lost

    @staticmethod
    def _centroid(bbox: Tuple[int, int, int, int]) -> Tuple[int, int]:
        x, y, w, h = bbox
        return (x + w // 2, y + h // 2)

    def update(self, detections: List[Tuple[int, int, int, int]], frame_index: int) -> List[Track]:
        if not self.tracks:
            for bbox in detections:
                centroid = self._centroid(bbox)
                self.tracks[self.next_id] = Track(self.next_id, bbox, centroid, frame_index)
                self.next_id += 1
            return list(self.tracks.values())

        track_ids = list(self.tracks.keys())
        track_centroids = np.array([self.tracks[t].centroid for t in track_ids])
        det_centroids = np.array([self._centroid(b) for b in detections]) if detections else np.empty((0, 2))

        if len(det_centroids) == 0:
            # Only age existing tracks
            to_delete = []
            for tid, tr in self.tracks.items():
                if frame_index - tr.last_seen_frame > self.max_lost:
                    to_delete.append(tid)
            for tid in to_delete:
                del self.tracks[tid]
            return list(self.tracks.values())

        # Compute distance matrix
        dists = np.linalg.norm(track_centroids[:, None, :] - det_centroids[None, :, :], axis=2)

        # Greedy assignment
        assigned_tracks = set()
        assigned_dets = set()
        for _ in range(min(len(track_ids), len(detections))):
            idx = np.unravel_index(np.argmin(dists, axis=None), dists.shape)
            ti, di = idx
            if dists[ti, di] > 80:  # distance gating
                break
            tid = track_ids[ti]
            self.tracks[tid].bbox = detections[di]
            self.tracks[tid].centroid = self._centroid(detections[di])
            self.tracks[tid].last_seen_frame = frame_index
            assigned_tracks.add(ti)
            assigned_dets.add(di)
            dists[ti, :] = np.inf
            dists[:, di] = np.inf

        # Create new tracks for unassigned detections
        for di, bbox in enumerate(detections):
            if di in assigned_dets:
                continue
            centroid = self._centroid(bbox)
            self.tracks[self.next_id] = Track(self.next_id, bbox, centroid, frame_index)
            self.next_id += 1

        # Remove lost tracks
        to_delete = []
        for tid, tr in self.tracks.items():
            if frame_index - tr.last_seen_frame > self.max_lost:
                to_delete.append(tid)
        for tid in to_delete:
            del self.tracks[tid]

        return list(self.tracks.values())

