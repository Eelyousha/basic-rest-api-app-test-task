import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees).
    Returns distance in meters.
    """
    R = 6371000  # Earth's radius in meters

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def is_in_bounding_box(lat: float, lon: float,
                       lat_min: float, lat_max: float,
                       lon_min: float, lon_max: float) -> bool:
    """
    Check if a point is within a bounding box.
    """
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


def calculate_bounding_box(lat: float, lon: float, radius: float) -> dict:
    """
    Calculate bounding box (lat_min, lat_max, lon_min, lon_max) for a given point and radius.
    Radius is in meters.
    Returns a dict with lat_min, lat_max, lon_min, lon_max.
    """
    R = 6371000  # Earth's radius in meters

    # Convert radius from meters to radians
    radius_rad = radius / R

    # Calculate latitude boundaries (straightforward)
    lat_rad = math.radians(lat)
    lat_min = math.degrees(lat_rad - radius_rad)
    lat_max = math.degrees(lat_rad + radius_rad)

    # Calculate longitude boundaries (adjust for latitude)
    # At higher latitudes, degrees of longitude represent shorter distances
    lon_rad = math.radians(lon)
    delta_lon = math.asin(math.sin(radius_rad) / math.cos(lat_rad))
    lon_min = math.degrees(lon_rad - delta_lon)
    lon_max = math.degrees(lon_rad + delta_lon)

    return {
        "lat_min": lat_min,
        "lat_max": lat_max,
        "lon_min": lon_min,
        "lon_max": lon_max
    }
