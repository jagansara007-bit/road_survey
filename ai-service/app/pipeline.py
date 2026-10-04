import logging
from collections.abc import Callable
from typing import Any

import cv2
from app.dedup import dedup_tracks
from app.gps import filter_gps, parse_csv, parse_gpx
from app.schemas import Defect, TrackObservation
from app.tracker import Tracker, group_into_tracks

logger = logging.getLogger(__name__)


def process_video(
    video_path: str,
    gps_path: str,
    tracker: Tracker,
    cfg: dict[str, Any],
    progress_cb: Callable[[int, int], None] | None = None
) -> tuple[list[Defect], list[list[TrackObservation]]]:
    """
    Orchestrates video processing, GPS parsing, tracking, and deduplication.
    """
    # 1. Parse GPS
    gps_points = []
    if gps_path.lower().endswith(".csv"):
        gps_points, _malformed = parse_csv(gps_path)
    elif gps_path.lower().endswith(".gpx"):
        gps_points, _malformed = parse_gpx(gps_path)
    else:
        raise ValueError("Unsupported GPS file format. Use .csv or .gpx")
        
    gps_points = filter_gps(gps_points, cfg.get("gps", {}))
    
    # 2. Extract frames and track
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise OSError(f"Cannot open video {video_path}")
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0
        
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    frame_stride = cfg.get("tracking", {}).get("frame_stride", 1)
    
    detections_stream = []
    frame_idx = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_idx % frame_stride == 0:
            dets = tracker.track(frame, frame_idx)
            detections_stream.append((frame_idx, dets))
            
        frame_idx += 1
        if progress_cb and frame_idx % 10 == 0:
            progress_cb(frame_idx, total_frames)
            
    cap.release()
    
    if progress_cb:
        progress_cb(total_frames, total_frames)
        
    # 3. Group detections into tracks
    min_track_frames = cfg.get("tracking", {}).get("min_track_frames", 3)
    tracks = group_into_tracks(detections_stream, frame_w, frame_h, min_track_frames)
    
    # 4. Dedup tracks and assign GPS
    video_start_offset_s = cfg.get("gps", {}).get("video_start_offset_s", 0.0)
    located_defects, unlocated_tracks = dedup_tracks(tracks, gps_points, fps, video_start_offset_s, cfg)
    
    if unlocated_tracks:
        logger.warning(f"Failed to locate {len(unlocated_tracks)} tracks due to missing GPS coverage.")
        
    return located_defects, unlocated_tracks
