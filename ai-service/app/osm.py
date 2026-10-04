import json
import logging
from typing import Protocol

from app.gps import haversine_m

logger = logging.getLogger(__name__)


class RoadContext(Protocol):
    def road_class(self, lat: float, lon: float) -> str:
        ...

    def near_sensitive(self, lat: float, lon: float, radius_m: float) -> bool:
        ...


class CachedOsmProvider:
    """
    Offline OSM provider reading a local GeoJSON/JSON cache.
    No network calls inside the service.
    """

    def __init__(self, cache_file: str, default_class: str = "residential"):
        self.default_class = default_class
        self.highways = []
        self.amenities = []
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.highways = data.get("highways", [])
                self.amenities = data.get("amenities", [])
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load OSM cache from {cache_file}: {e}")

    def road_class(self, lat: float, lon: float) -> str:
        # Simplistic approach: find nearest highway segment
        best_dist = float("inf")
        best_class = self.default_class

        for h in self.highways:
            # We assume highways is a list of {"tags": {"highway": "..."}, "geometry": [[lat, lon], ...]}
            h_class = h.get("tags", {}).get("highway", self.default_class)
            for pt in h.get("geometry", []):
                d = haversine_m(lat, lon, pt[0], pt[1])
                if d < best_dist:
                    best_dist = d
                    best_class = h_class

        # Only trust it if we're reasonably close (e.g., 50 meters)
        if best_dist <= 50.0:
            return best_class
        return self.default_class

    def near_sensitive(self, lat: float, lon: float, radius_m: float) -> bool:
        for a in self.amenities:
            # amenities: {"tags": {"amenity": "..."}, "lat": ..., "lon": ...}
            a_lat = a.get("lat")
            a_lon = a.get("lon")
            if a_lat is not None and a_lon is not None:
                d = haversine_m(lat, lon, a_lat, a_lon)
                if d <= radius_m:
                    return True
        return False
