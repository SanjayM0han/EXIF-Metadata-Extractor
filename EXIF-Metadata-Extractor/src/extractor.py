import piexif
from pillow_heif import register_heif_opener
from PIL import Image

# Enable HEIC support
register_heif_opener()

def extract_exif(image_path):
    """
    Extract EXIF metadata using piexif for accurate GPS reading.
    """
    try:
        exif_dict = piexif.load(image_path)  # TRUE EXIF extraction
    except Exception as e:
        print("[ERROR] Cannot load EXIF:", e)
        return {}

    metadata = {}

    # Loop through all EXIF dictionaries
    for ifd in ("0th", "Exif", "GPS", "1st"):
        if ifd not in exif_dict:
            continue

        for tag_id, value in exif_dict[ifd].items():
            tag_name = piexif.TAGS[ifd][tag_id]["name"]
            metadata[tag_name] = value

    return metadata


if __name__ == "__main__":
    data = extract_exif("../samples/gps_sample.jpg")
    for k, v in data.items():
        print(f"{k}: {v}")
