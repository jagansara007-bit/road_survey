import argparse
import json
import logging
import urllib.parse
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_cache(min_lat: float, min_lon: float, max_lat: float, max_lon: float, output_path: str):
    bbox = f"{min_lat},{min_lon},{max_lat},{max_lon}"
    query = f"""
    [out:json];
    (
      way["highway"]({bbox});
      node["amenity"~"school|hospital"]({bbox});
    );
    out geom;
    """
    
    url = "http://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({'data': query}).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    
    logger.info(f"Querying Overpass API for bbox {bbox}...")
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        highways = []
        amenities = []
        
        for element in result.get("elements", []):
            if element["type"] == "way" and "tags" in element and "highway" in element["tags"]:
                geometry = [[pt["lat"], pt["lon"]] for pt in element.get("geometry", [])]
                highways.append({
                    "tags": element["tags"],
                    "geometry": geometry
                })
            elif element["type"] == "node" and "tags" in element and "amenity" in element["tags"]:
                amenities.append({
                    "tags": element["tags"],
                    "lat": element["lat"],
                    "lon": element["lon"]
                })
                
        cache_data = {
            "highways": highways,
            "amenities": amenities
        }
        
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)
            
        logger.info(f"Saved {len(highways)} highways and {len(amenities)} amenities to {output_path}")
        
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        logger.error(f"Failed to build OSM cache: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build OSM cache for offline road context")
    parser.add_argument("--min_lat", type=float, required=True)
    parser.add_argument("--min_lon", type=float, required=True)
    parser.add_argument("--max_lat", type=float, required=True)
    parser.add_argument("--max_lon", type=float, required=True)
    parser.add_argument("--output", type=str, default="data/osm_cache/default.json")
    
    args = parser.parse_args()
    build_cache(args.min_lat, args.min_lon, args.max_lat, args.max_lon, args.output)
