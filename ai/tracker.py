"""
Person ReID Tracker — assigns stable track IDs across frames.

Wraps `deep-sort-realtime` DeepSort tracker. Integrates with YOLOv8
person detections to produce identity-annotated bounding boxes.
"""

import threading

from utils.config import (
    TRACKER_MAX_AGE,
    TRACKER_N_INIT,
    TRACKER_MAX_COSINE_DIST,
)


class PersonTrack:
    """Represents a tracked person in a single frame."""

    def __init__(self, x1: int, y1: int, x2: int, y2: int,
                 confidence: float, track_id: int, cls_id: int = 0):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.confidence = confidence
        self.track_id = track_id
        self.cls_id = cls_id

    @property
    def center(self):
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    @property
    def width(self):
        return self.x2 - self.x1

    @property
    def height(self):
        return self.y2 - self.y1

    @property
    def area(self):
        return self.width * self.height


class PersonTrackManager:
    """
    Manages person ReID tracking via DeepSORT.

    Usage:
        tracker = PersonTrackManager()
        results = tracker.update(frame, detections)
        # detections: list of [x1, y1, x2, y2, confidence]
        for track in results:
            print(f"Person {track.track_id}: {track.x1},{track.y1}-{track.x2},{track.y2}")
    """

    def __init__(self, max_age=TRACKER_MAX_AGE, n_init=TRACKER_N_INIT,
                 max_cosine_dist=TRACKER_MAX_COSINE_DIST):
        self._max_age = max_age
        self._n_init = n_init
        self._max_cosine_dist = max_cosine_dist

        # Lazy init — DeepSort loads ReID model on first use
        self._deepsort = None
        self._lock = threading.Lock()

    def _ensure_tracker(self):
        """Load deep-sort-realtime tracker on first use."""
        if self._deepsort is None:
            from deep_sort_realtime.deepsort_tracker import DeepSort
            self._deepsort = DeepSort(
                max_age=self._max_age,
                n_init=self._n_init,
                max_cosine_distance=self._max_cosine_dist,
                embedder="mobilenet",
                embedder_gpu=False,  # CPU-only
            )

    def update(self, frame, detections):
        """
        Process YOLO person detections with ReID tracking.

        Args:
            frame: numpy image (H, W, C) — needed for ReID embedding extraction
            detections: list of [x1, y1, x2, y2, confidence]

        Returns:
            list of PersonTrack with stable track_ids
        """
        if not detections:
            return []

        self._ensure_tracker()

        # deep-sort-realtime expects [x1, y1, w, h] format
        raw_dets = [
            ([float(d[0]), float(d[1]), float(d[2]) - float(d[0]), float(d[3]) - float(d[1])],
             float(d[4]),
             "person")
            for d in detections
        ]

        # update_tracks returns list of Track objects
        tracks = self._deepsort.update_tracks(
            raw_dets,
            frame=frame,
        )

        results = []
        for track in tracks:
            # Skip deleted tracks
            if track.is_deleted():
                continue

            # Only include tracks that matched a detection this frame
            # (tracks predicted without detection match would be stale)
            if track.get_det_conf() is None:
                continue

            # Use original detection box, fall back to KF-predicted
            tlbr = track.to_tlbr(orig=True, orig_strict=False)
            if tlbr is None:
                tlbr = track.to_tlbr(orig=False)

            person_track = PersonTrack(
                x1=int(tlbr[0]),
                y1=int(tlbr[1]),
                x2=int(tlbr[2]),
                y2=int(tlbr[3]),
                confidence=float(track.get_det_conf() or 0.0),
                track_id=int(track.track_id),
                cls_id=0,
            )
            results.append(person_track)

        return results

    def clear(self):
        """Reset all tracked persons."""
        if self._deepsort is not None:
            self._deepsort.delete_all_tracks()
        self._deepsort = None
