import os
import cv2
import numpy as np

output_dir = r"C:\Users\jagan\.gemini\antigravity-ide\scratch\road-damage-system\sample_upload"
os.makedirs(output_dir, exist_ok=True)
video_path = os.path.join(output_dir, "sample_road_survey.mp4")
gps_path = os.path.join(output_dir, "sample_road_gps.csv")

# 1. Generate Video
fps = 30
duration_sec = 10
total_frames = fps * duration_sec
width, height = 1280, 720

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))

start_time = 1700000000.0
speed_kmh = 32.0

# Road geometry
horizon_y = int(height * 0.42)
road_top_left = int(width * 0.45)
road_top_right = int(width * 0.55)
road_bottom_left = int(width * 0.05)
road_bottom_right = int(width * 0.95)

# Pothole schedule (frame_start, frame_end, lane: -1=left, 1=right)
potholes = [
    {"start": 30, "duration": 80, "lane": -0.3, "size": 35},
    {"start": 130, "duration": 90, "lane": 0.4, "size": 45},
    {"start": 210, "duration": 80, "lane": -0.1, "size": 40},
]

for f in range(total_frames):
    t = f / fps
    curr_time = start_time + t
    
    # Background: Sky & Ground
    frame = np.full((height, width, 3), (210, 195, 175), dtype=np.uint8) # Sky
    frame[horizon_y:, :] = (60, 110, 60) # Greenish roadside terrain
    
    # Road Asphalt Trapezoid
    road_poly = np.array([
        [road_top_left, horizon_y],
        [road_top_right, horizon_y],
        [road_bottom_right, height - 40],
        [road_bottom_left, height - 40]
    ], np.int32)
    cv2.fillPoly(frame, [road_poly], (55, 55, 55))
    
    # Asphalt Texture noise
    noise = np.random.randint(-8, 8, (height - horizon_y - 40, width, 3), dtype=np.int16)
    road_patch = frame[horizon_y:height - 40, :].astype(np.int16) + noise
    frame[horizon_y:height - 40, :] = np.clip(road_patch, 0, 255).astype(np.uint8)
    
    # Road Edges (solid white lines)
    cv2.line(frame, (road_top_left, horizon_y), (road_bottom_left, height - 40), (220, 220, 220), 4)
    cv2.line(frame, (road_top_right, horizon_y), (road_bottom_right, height - 40), (220, 220, 220), 4)
    
    # Center Dashed Line (moving forward)
    dash_length = 50
    gap_length = 50
    cycle = dash_length + gap_length
    offset = (f * 12) % cycle
    
    for y_screen in range(horizon_y + 10, height - 40, 20):
        # Progress from horizon (0.0) to bottom (1.0)
        p = (y_screen - horizon_y) / (height - 40 - horizon_y)
        # Non-linear perspective scaling
        p_curv = p ** 1.8
        world_y = int(p_curv * 500) + int(f * 14)
        if (world_y % cycle) < dash_length:
            center_x = int(width * 0.5)
            w_line = max(2, int(p * 8))
            cv2.line(frame, (center_x, y_screen), (center_x, min(height - 40, y_screen + 15)), (230, 230, 230), w_line)
            
    # Draw Potholes passing by
    for p_info in potholes:
        if p_info["start"] <= f < (p_info["start"] + p_info["duration"]):
            prog = (f - p_info["start"]) / p_info["duration"]
            # Appears near horizon and moves towards bottom
            p_y = int(horizon_y + (height - horizon_y - 60) * (prog ** 1.6))
            norm_y = (p_y - horizon_y) / (height - horizon_y)
            center_x = int(width * 0.5 + p_info["lane"] * (width * 0.38) * norm_y)
            rad_x = int(p_info["size"] * (0.3 + 0.9 * norm_y))
            rad_y = int(rad_x * 0.5)
            
            # Pothole cavity (dark rough ellipse)
            cv2.ellipse(frame, (center_x, p_y), (rad_x, rad_y), 0, 0, 360, (25, 25, 25), -1)
            # Edge rim highlighting
            cv2.ellipse(frame, (center_x, p_y), (rad_x, rad_y), 0, 0, 360, (75, 75, 75), 2)
            cv2.ellipse(frame, (center_x - 2, p_y - 1), (int(rad_x * 0.8), int(rad_y * 0.7)), 0, 0, 360, (15, 15, 15), -1)

    # Longitudinal and alligator cracks
    if 50 < f < 180:
        cr_prog = (f - 50) / 130
        cr_y = int(horizon_y + (height - horizon_y - 70) * (cr_prog ** 1.5))
        cr_x = int(width * 0.55 + 60 * (cr_y - horizon_y) / (height - horizon_y))
        cv2.line(frame, (cr_x, cr_y), (cr_x + 8, cr_y + 25), (20, 20, 20), 2)
        cv2.line(frame, (cr_x + 8, cr_y + 25), (cr_x + 3, cr_y + 50), (20, 20, 20), 2)

    # Vehicle Hood Line (extreme bottom)
    hood_poly = np.array([
        [0, height],
        [width, height],
        [width, height - 35],
        [int(width * 0.8), height - 42],
        [int(width * 0.2), height - 42],
        [0, height - 35]
    ], np.int32)
    cv2.fillPoly(frame, [hood_poly], (30, 30, 35))
    cv2.polylines(frame, [hood_poly], False, (70, 70, 80), 2)
    
    # Dashcam HUD
    cv2.rectangle(frame, (20, 20), (420, 75), (0, 0, 0), -1)
    cv2.rectangle(frame, (20, 20), (420, 75), (0, 255, 255), 1)
    hud_text1 = f"CAM-01 CHENNAI SURVEY  {t:.1f}s / {duration_sec}s"
    hud_text2 = f"SPEED: {speed_kmh:.1f} km/h   GPS: 3D FIX"
    cv2.putText(frame, hud_text1, (30, 43), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    cv2.putText(frame, hud_text2, (30, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)

    out.write(frame)

out.release()

# 2. Generate Synchronized GPS CSV
# Driving North along Anna Salai, Chennai (approx 32 km/h = 8.88 m/s)
# 1 deg lat ~= 111,000 meters -> 8.88 m ~= 0.00008 deg lat per second
lat_start = 13.006700
lon_start = 80.220600

with open(gps_path, "w") as fgps:
    fgps.write("timestamp,lat,lon,accuracy_m,speed\n")
    for sec in range(duration_sec + 1):
        ts = start_time + sec
        lat = lat_start + sec * 0.000080
        lon = lon_start + sec * 0.000015
        fgps.write(f"{ts:.1f},{lat:.6f},{lon:.6f},1.8,{speed_kmh:.1f}\n")

print(f"Generated Video: {video_path}")
print(f"Generated GPS CSV: {gps_path}")
