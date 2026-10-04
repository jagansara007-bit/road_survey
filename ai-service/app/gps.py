import csv
import logging
import math
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

from app.schemas import GPSPoint

logger = logging.getLogger(__name__)

def parse_csv(filepath: str) -> tuple[list[GPSPoint], int]:
    points = []
    malformed_count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Handle timestamp
                ts_str = row["timestamp"]
                try:
                    # Epoch
                    ts = float(ts_str)
                except ValueError:
                    # ISO8601
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()

                lat = float(row["lat"])
                lon = float(row["lon"])
                
                acc = float(row["accuracy_m"]) if row.get("accuracy_m") else None
                speed = float(row["speed"]) if row.get("speed") else None
                
                points.append(GPSPoint(timestamp_s=ts, lat=lat, lon=lon, accuracy_m=acc, speed_mps=speed))
            except Exception as e:  # noqa: BLE001
                malformed_count += 1
                logger.warning(f"Malformed CSV row: {row}. Error: {e}")
    return points, malformed_count


def parse_gpx(filepath: str) -> tuple[list[GPSPoint], int]:
    points = []
    malformed_count = 0
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        # GPX namespace usually xmlns="http://www.topografix.com/GPX/1/1"
        ns = {"gpx": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {"gpx": ""}
        ns_prefix = "gpx:" if ns.get("gpx") else ""
        
        for trkpt in root.findall(f".//{ns_prefix}trkpt", ns):
            try:
                lat = float(trkpt.attrib["lat"])
                lon = float(trkpt.attrib["lon"])
                
                time_node = trkpt.find(f"{ns_prefix}time", ns)
                if time_node is None or not time_node.text:
                    raise ValueError("Missing time")
                ts = datetime.fromisoformat(time_node.text.replace("Z", "+00:00")).timestamp()
                
                # Accuracy/Speed are non-standard in base GPX 1.1, often under extensions
                points.append(GPSPoint(timestamp_s=ts, lat=lat, lon=lon))
            except Exception as e:  # noqa: BLE001
                malformed_count += 1
                logger.warning(f"Malformed GPX trkpt: {trkpt.attrib}. Error: {e}")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to parse GPX: {e}")
    return points, malformed_count


def filter_gps(points: list[GPSPoint], cfg: dict[str, Any]) -> list[GPSPoint]:
    max_acc = cfg.get("max_accuracy_m")
    if not max_acc:
        return points
    return [p for p in points if p.accuracy_m is None or p.accuracy_m <= max_acc]


def interpolate(points: list[GPSPoint], video_time_s: float, video_start_offset_s: float, cfg: dict[str, Any]) -> GPSPoint | None:
    if not points:
        return None
        
    gps_time_s = video_time_s + video_start_offset_s
    max_gap = cfg.get("max_time_gap_s", 5.0)
    
    # Binary search or simple linear scan
    if gps_time_s < points[0].timestamp_s or gps_time_s > points[-1].timestamp_s:
        return None
        
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        if p1.timestamp_s <= gps_time_s <= p2.timestamp_s:
            gap = p2.timestamp_s - p1.timestamp_s
            if gap > max_gap:
                return None
            if gap == 0:
                return p1
                
            ratio = (gps_time_s - p1.timestamp_s) / gap
            lat = p1.lat + ratio * (p2.lat - p1.lat)
            lon = p1.lon + ratio * (p2.lon - p1.lon)
            return GPSPoint(timestamp_s=gps_time_s, lat=lat, lon=lon)
            
    return None


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def project_to_metric(lat: float, lon: float, centroid_lat: float, centroid_lon: float) -> tuple[float, float]:
    """
    Equirectangular projection around a centroid.
    Error bound: For city-scale distances (< 50km), distortion is negligible (< 0.1%).
    """
    R = 6371000.0
    x_m = R * math.radians(lon - centroid_lon) * math.cos(math.radians(centroid_lat))
    y_m = R * math.radians(lat - centroid_lat)
    return x_m, y_m


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns bearing in degrees from North."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)
    
    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    theta = math.atan2(y, x)
    return (math.degrees(theta) + 360) % 360


def shift_position(lat: float, lon: float, bearing_deg: float, distance_m: float) -> tuple[float, float]:
    R = 6371000.0
    bearing_rad = math.radians(bearing_deg)
    phi1 = math.radians(lat)
    lambda1 = math.radians(lon)
    
    phi2 = math.asin(math.sin(phi1) * math.cos(distance_m / R) +
                     math.cos(phi1) * math.sin(distance_m / R) * math.cos(bearing_rad))
    lambda2 = lambda1 + math.atan2(math.sin(bearing_rad) * math.sin(distance_m / R) * math.cos(phi1),
                                   math.cos(distance_m / R) - math.sin(phi1) * math.sin(phi2))
    return math.degrees(phi2), math.degrees(lambda2)
