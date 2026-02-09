from PIL.ExifTags import GPSTAGS


def extract_gps(exif):
    """
    Extract GPS info safely from piexif EXIF data.
    Returns None if GPS block is incomplete or corrupted.
    """
    required = ["GPSLatitude", "GPSLatitudeRef", "GPSLongitude", "GPSLongitudeRef"]

    # Check if keys exist
    if not all(key in exif for key in required):
        return None

    gps = {}
    try:
        gps["GPSLatitude"] = exif["GPSLatitude"]
        gps["GPSLongitude"] = exif["GPSLongitude"]
        gps["GPSLatitudeRef"] = exif["GPSLatitudeRef"].decode()
        gps["GPSLongitudeRef"] = exif["GPSLongitudeRef"].decode()
    except Exception:
        return None

    return gps


def _safe_rational(r):
    """
    Convert rational tuple safely: returns None on zero or invalid data.
    Example: (x,0) → None
    """
    num, den = r
    if den == 0:
        return None
    return num / den


def _convert_to_degrees(value):
    """
    Converts GPS coordinates from DMS to decimal safely.
    Returns None if conversion is impossible.
    """
    d = _safe_rational(value[0])
    m = _safe_rational(value[1])
    s = _safe_rational(value[2])

    if d is None or m is None or s is None:
        return None

    return d + (m / 60.0) + (s / 3600.0)


def get_lat_long(gps):
    """
    Safely compute latitude and longitude.
    Returns (None, None) if conversion is invalid.
    """
    lat = _convert_to_degrees(gps["GPSLatitude"])
    lon = _convert_to_degrees(gps["GPSLongitude"])

    # If conversion failed
    if lat is None or lon is None:
        return None, None

    if gps["GPSLatitudeRef"] != "N":
        lat = -lat
    if gps["GPSLongitudeRef"] != "E":
        lon = -lon

    return lat, lon
