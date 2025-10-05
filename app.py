import os
import tempfile
import zipfile
import base64
from PIL import Image, ExifTags
import simplekml
import streamlit as st
from datetime import datetime

def get_base64_image(image_path):
    """Convert image to base64 string for embedding in HTML."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def correct_image_orientation(image):
    """Correct image orientation based on Exif data."""
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == "Orientation":
                break

        exif = image._getexif()
        if exif and orientation in exif:
            if exif[orientation] == 3:
                image = image.rotate(180, expand=True)
            elif exif[orientation] == 6:
                image = image.rotate(270, expand=True)
            elif exif[orientation] == 8:
                image = image.rotate(90, expand=True)
    except Exception as e:
        st.warning(f"Could not adjust image orientation: {e}")
    return image

def convert_to_degrees(value):
    """Convert GPS coordinates to degrees."""
    try:
        d = float(value[0][0]) / float(value[0][1]) if isinstance(value[0], tuple) else float(value[0])
        m = float(value[1][0]) / float(value[1][1]) if isinstance(value[1], tuple) else float(value[1])
        s = float(value[2][0]) / float(value[2][1]) if isinstance(value[2], tuple) else float(value[2])
        return d + (m / 60.0) + (s / 3600.0)
    except Exception as e:
        st.warning(f"Error converting GPS value to degrees: {e}")
        return None

def get_gps_metadata(image_path):
    """Extract GPS metadata from a JPEG/PNG image."""
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        if not exif_data:
            return None

        gps_info = {}
        date_taken = None
        
        # Extract all EXIF data including date and GPS info
        for tag, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag, tag)
            if tag_name == "GPSInfo":
                for t, val in value.items():
                    gps_tag = ExifTags.GPSTAGS.get(t, t)
                    gps_info[gps_tag] = val
            elif tag_name in ["DateTime", "DateTimeOriginal", "DateTimeDigitized"]:
                # Try to get the original date the photo was taken
                try:
                    if tag_name == "DateTimeOriginal":  # This is the preferred date
                        date_taken = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                    elif not date_taken and tag_name == "DateTime":  # Fallback to DateTime
                        date_taken = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                    elif not date_taken and tag_name == "DateTimeDigitized":  # Second fallback
                        date_taken = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    continue

        # If no date found in EXIF, fall back to file creation time
        if not date_taken:
            date_taken = datetime.fromtimestamp(os.path.getctime(image_path)).strftime('%Y-%m-%d %H:%M:%S')

        if not gps_info:
            return None

        if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
            lat = convert_to_degrees(gps_info["GPSLatitude"])
            lon = convert_to_degrees(gps_info["GPSLongitude"])
            if gps_info["GPSLatitudeRef"] == "S":
                lat = -lat
            if gps_info["GPSLongitudeRef"] == "W":
                lon = -lon

            altitude = gps_info.get("GPSAltitude", (0, 1))  # Default to 0 if not available
            alt = float(altitude[0]) / float(altitude[1]) if isinstance(altitude, tuple) else float(altitude)

            return {
                "latitude": lat,
                "longitude": lon,
                "altitude": alt,
                "orientation": gps_info.get("GPSImgDirection", 0),
                "date_created": date_taken,
            }
        return None
    except Exception as e:
        st.error(f"Error extracting metadata from {image_path}: {e}")
        return None

def create_kmz_with_fan_overlay(folder_path, output_kmz, fan_image_path):
    """Generate a KMZ file with fan overlays and placemarks."""
    kml = simplekml.Kml()
    image_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    kmz_images = []
    has_data = False

    for image_path in image_paths:
        metadata = get_gps_metadata(image_path)
        if metadata:
            has_data = True
            lat, lon, alt = metadata["latitude"], metadata["longitude"], metadata["altitude"]
            orientation = float(metadata["orientation"])
            date_created = metadata["date_created"]
            image_name = os.path.basename(image_path)

            # Correct image orientation
            image = Image.open(image_path)
            corrected_image = correct_image_orientation(image)
            corrected_image_path = os.path.join(folder_path, image_name)
            corrected_image.save(corrected_image_path)

            # Define overlay dimensions
            overlay_size = 0.0001  # Adjust this to control the overlay size
            north = lat + overlay_size / 2
            south = lat - overlay_size / 2
            east = lon + overlay_size / 2
            west = lon - overlay_size / 2

            # Add a GroundOverlay for Fan.png
            ground_overlay = kml.newgroundoverlay(name=f"Overlay - {image_name}")
            ground_overlay.icon.href = "Fan.png"
            ground_overlay.latlonbox.north = north
            ground_overlay.latlonbox.south = south
            ground_overlay.latlonbox.east = east
            ground_overlay.latlonbox.west = west
            ground_overlay.latlonbox.rotation = -abs(orientation)  # Ensure the orientation is always negative

            # Create a placemark description with metadata
            placemark_description = f"""
            <html>
            <head>
                <title></title>
                <style>
                    table {{
                        width: 100%;
                        text-align: center;
                        border-collapse: collapse;
                    }}
                    th, td {{
                        border: 1px solid black;
                        padding: 5px;
                    }}
                    th {{
                        background-color: grey;
                        color: white;
                    }}
                </style>
            </head>
            <body>
                <h1>
                    <img src="Construct_Solutions_Logo_HALF.png" alt="Construct Solutions Logo" style="height: 50px;">
                </h1>
                <table>
                    <thead>
                        <tr>
                            <th>DATE CREATED</th>
                            <th>ALTITUDE</th>
                            <th>ORIENTATION</th>
                            <th>LATITUDE</th>
                            <th>LONGITUDE</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>{date_created}</td>
                            <td>{alt:.1f} Meters</td>
                            <td>{orientation:.1f}°</td>
                            <td>{lat:.6f}</td>
                            <td>{lon:.6f}</td>
                        </tr>
                    </tbody>
                </table>
                <div>
                    <img src="{image_name}" alt="Image" width="800" />
                </div>
            </body>
            </html>
            """

            # Add placemark to KML
            pnt = kml.newpoint(name=image_name, coords=[(lon, lat, alt)])
            pnt.description = placemark_description
            pnt.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/paddle/blu-circle.png"
            pnt.altitudemode = simplekml.AltitudeMode.absolute

            kmz_images.append((image_name, corrected_image_path))

    if not has_data:
        raise ValueError("No valid GPS metadata found in the uploaded images.")

    # Save fan image
    fan_image_dest = os.path.join(folder_path, "Fan.png")
    if os.path.exists(fan_image_path):
        os.rename(fan_image_path, fan_image_dest)

    # Save company logo
    logo_src = "Construct_Solutions_Logo_HALF.png"
    logo_dest = os.path.join(folder_path, "Construct_Solutions_Logo_HALF.png")
    if os.path.exists(logo_src):
        import shutil
        shutil.copy2(logo_src, logo_dest)

    # Save KML file
    kml_file = os.path.join(folder_path, "doc.kml")
    kml.save(kml_file)

    # Package KMZ file
    with zipfile.ZipFile(output_kmz, 'w') as kmz:
        kmz.write(kml_file, "doc.kml")
        for img_name, img_path in kmz_images:
            kmz.write(img_path, img_name)
        if os.path.exists(fan_image_dest):
            kmz.write(fan_image_dest, "Fan.png")
        if os.path.exists(logo_dest):
            kmz.write(logo_dest, "Construct_Solutions_Logo_HALF.png")

    os.remove(kml_file)

# Streamlit app configuration
st.set_page_config(page_title="KMZ Generator - Construct Solutions", layout="wide")

# Display company logo
if os.path.exists("Construct_Solutions_Logo_HALF.png"):
    logo_base64 = get_base64_image("Construct_Solutions_Logo_HALF.png")
    st.markdown(
        f"""
        <div style="text-align: left; margin-top: 5px;">
            <img src="data:image/png;base64,{logo_base64}" alt="Construct Solutions Logo" style="height: 100px;">
        </div>
        """,
        unsafe_allow_html=True
    )

st.title("JPEG/PNG to KMZ Converter")
st.markdown("**Upload geotagged photos and generate KMZ files for Google Earth**")

# File uploader
uploaded_files = st.file_uploader(
    "Upload geotagged photos (JPG, JPEG, PNG):",
    accept_multiple_files=True,
    type=["jpg", "jpeg", "png"],
    help="Select multiple images that contain GPS location data in their EXIF metadata"
)

# Output filename input
output_kmz_name = st.text_input("Enter output KMZ file name:", "output.kmz")

# Generate KMZ button
if st.button("Generate KMZ", type="primary"):
    if not uploaded_files:
        st.error("Please upload at least one photo.")
    else:
        with st.spinner("Generating KMZ file, please wait..."):
            try:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    # Copy fan image to temp directory
                    fan_image_path = os.path.join(tmp_dir, "Fan.png")
                    if os.path.exists("Fan.png"):
                        import shutil
                        shutil.copy2("Fan.png", fan_image_path)

                    # Save uploaded files to temp directory
                    for uploaded_file in uploaded_files:
                        file_path = os.path.join(tmp_dir, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.read())

                    # Generate KMZ file
                    output_kmz_path = os.path.join(tmp_dir, output_kmz_name)
                    create_kmz_with_fan_overlay(tmp_dir, output_kmz_path, fan_image_path)

                    # Provide download button
                    with open(output_kmz_path, "rb") as f:
                        st.download_button(
                            label="📥 Download KMZ File",
                            data=f,
                            file_name=output_kmz_name,
                            mime="application/vnd.google-earth.kmz"
                        )
                st.success("KMZ file generated successfully!")
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Information section
with st.expander("ℹ️ How to use this tool"):
    st.markdown("""
    **Steps to generate a KMZ file:**
    
    1. **Upload Images**: Select one or more JPEG or PNG images that contain GPS location data
    2. **Enter Filename**: Specify a name for your KMZ output file
    3. **Generate**: Click the "Generate KMZ" button to process your images
    4. **Download**: Use the download button to save the KMZ file to your computer
    5. **View in Google Earth**: Open the downloaded KMZ file in Google Earth to see your images on the map
    
    **Requirements:**
    - Images must be in JPEG or PNG format
    - Images must contain GPS metadata (latitude and longitude) in their EXIF data
    - Images taken with smartphones or GPS-enabled cameras typically include this data
    """)
