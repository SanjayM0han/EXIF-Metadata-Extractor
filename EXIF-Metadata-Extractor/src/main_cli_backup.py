from extractor import extract_exif
from gps_utils import extract_gps, get_lat_long
import webbrowser


def print_clean_metadata(exif):
    """
    Print only important and readable EXIF metadata.
    """

    print("\n==============================")
    print("       IMPORTANT METADATA")
    print("==============================\n")

    important_keys = [
        "Make", "Model", "DateTime", "DateTimeOriginal",
        "Orientation", "XResolution", "YResolution", "ResolutionUnit",
        "Software", "HostComputer", "ExifVersion",
        "ExposureTime", "FNumber", "ISOSpeedRatings", "FocalLength"
    ]

    for key in important_keys:
        if key in exif:
            value = exif[key]

            # Decode bytes e.g., b'Apple' → Apple
            if isinstance(value, bytes):
                value = value.decode(errors="ignore")

            # Convert rational tuples like (72,1) → 72.0
            if (
                isinstance(value, tuple)
                and len(value) == 2
                and all(isinstance(n, int) for n in value)
            ):
                if value[1] != 0:
                    value = value[0] / value[1]
                else:
                    value = "Invalid"

            print(f"{key:20}: {value}")

    print("\n==============================")
    print("          GPS METADATA")
    print("==============================\n")


def run_app():
    print("\n==============================")
    print("     EXIF METADATA TOOL")
    print("==============================\n")

    image_path = input("Enter image path: ")

    print("\nExtracting EXIF metadata...\n")
    exif = extract_exif(image_path)

    if not exif:
        print("\n[INFO] No EXIF metadata found. Exiting.\n")
        return

    # Print important EXIF values
    print_clean_metadata(exif)

    # Extract GPS safely
    gps = extract_gps(exif)

    if gps:
        lat, lon = get_lat_long(gps)

        # If GPS exists but is corrupt
        if lat is None or lon is None:
            print("[INFO] GPS data exists but is incomplete or corrupted.")
            return

        print(f"Latitude            : {lat}")
        print(f"Longitude           : {lon}")

        # Safe altitude extraction
        if "GPSAltitude" in exif:
            alt_num, alt_den = exif["GPSAltitude"]
            if alt_den == 0:
                print("Altitude            : Invalid (corrupted EXIF value)")
            else:
                alt = alt_num / alt_den
                print(f"Altitude            : {alt} m")

        if "GPSTimeStamp" in exif:
            print(f"GPS Time            : {exif['GPSTimeStamp']}")

        if "GPSDateStamp" in exif:
            date = exif["GPSDateStamp"].decode()
            print(f"GPS Date            : {date}")

        # Google Maps output
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        print(f"\nGoogle Maps Link    : {maps_url}")

        open_map = input("\nOpen in Google Maps? (y/n): ")
        if open_map.lower() == "y":
            webbrowser.open(maps_url)

    else:
        print("[INFO] No GPS metadata available in this image.")


if __name__ == "__main__":
    run_app()
