# GPS Synchronization and Tracking

This document explains the time synchronization and spatial deduplication logic in Phase 4 of the Road Damage Detection System.

## Time Synchronization (Clock Offset)

Consumer dashcams and smartphones often write video files using their internal clocks, while GPS logs (GPX/CSV) use precise satellite time. 
If there is a drift or difference between the two, tracking defects and associating them with a lat/lon becomes inaccurate.

To fix this, the pipeline supports a `video_start_offset_s` configuration parameter.
This offset specifies the exact GPS timestamp (in seconds, e.g., epoch time) when the video started recording.
The GPS timestamp of any video frame $i$ is calculated as:
$$ t_{gps} = \frac{i}{fps} + \text{video\_start\_offset\_s} $$

## Accuracy Filtering and Interpolation

Consumer GPS can jump wildly. The system implements a filtering mechanism:
1. **Accuracy Filtering:** Any GPS point with a reported accuracy worse than `cfg.gps.max_accuracy_m` is discarded.
2. **Gap Avoidance:** We linearly interpolate the position for a given video frame timestamp. However, if the time gap between two valid GPS points exceeds `cfg.gps.max_time_gap_s`, we refuse to interpolate. The track is marked as `unlocated`.

## Drift Handling and Deduplication

Even with filtering, GPS drift is common. A stationary pothole viewed across 30 consecutive video frames might theoretically map to 30 slightly different GPS locations as the vehicle moves or the GPS drifts.

To resolve this:
1. We group bounding boxes into tracks (via tracker ID).
2. We evaluate the single "closest approach" frame for the defect (the frame where the box area is largest and lowest in the view).
3. We extract a single interpolated GPS coordinate for that precise frame.
4. If the tracker loses the object and creates a new track ID (ID switch), we use single-linkage clustering. Tracks of the same class that are within `cfg.dedup.merge_radius_m` are merged into a single `Defect` object. 

## Known Limitation: Physical Defect Location vs. Camera Location

**Limitation:** The latitude and longitude recorded for a defect is fundamentally the position of the *camera (phone/vehicle)* at the time of closest approach, **not** the physical location of the pothole itself. 

While the system calculates the bearing of the vehicle and can theoretically project the coordinate forward by a configurable `camera_forward_offset_m`, this is an estimate. It relies on the assumption that the defect is directly in front of the vehicle. Precise physical geometry mapping (e.g., using photogrammetry or stereo depth mapping) is out of scope for this system.
