from PIL import Image
import piexif

# Create a simple image
img = Image.new("RGB", (600, 400), color=(255, 200, 100))
img.save("samples/gps_sample.jpg")

# GPS coordinates (Example: New York City)
gps_lat_deg = (40, 1)
gps_lat_min = (42, 1)
gps_lat_sec = (51, 1)

gps_lon_deg = (74, 1)
gps_lon_min = (0, 1)
gps_lon_sec = (21, 1)

exif_dict = {
    "GPS": {
        piexif.GPSIFD.GPSLatitudeRef: b"N",
        piexif.GPSIFD.GPSLatitude: [gps_lat_deg, gps_lat_min, gps_lat_sec],
        piexif.GPSIFD.GPSLongitudeRef: b"W",
        piexif.GPSIFD.GPSLongitude: [gps_lon_deg, gps_lon_min, gps_lon_sec],
    }
}

exif_bytes = piexif.dump(exif_dict)
piexif.insert(exif_bytes, "samples/gps_sample.jpg")

print("GPS-enabled sample image created: samples/gps_sample.jpg")
