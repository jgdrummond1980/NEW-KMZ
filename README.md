# Image to KMZ Converter - Construct Solutions

This web application allows you to upload a collection of images (JPEG or PNG) with GPS metadata and generate a KMZ file that can be opened in Google Earth. The KMZ file will display each image as a placemark at its corresponding geographic location.

## Features

The application extracts GPS latitude, longitude, and altitude from EXIF data and creates a KMZ file with placemarks for each image. It displays a custom fan icon overlay for each image, oriented according to the image's GPS direction, and shows a popup balloon in Google Earth with image metadata and a preview of the image.

## Installation and Setup

To run this application locally, you need Python 3.7 or higher installed on your system.

**Clone or download this repository and navigate to the project directory:**

```bash
cd image-to-kmz-converter
```

**Install the required dependencies:**

```bash
pip install -r requirements.txt
```

**Run the application:**

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## Usage Instructions

The application provides a simple web interface for converting geotagged images to KMZ format. Upload multiple images at once using the file uploader, ensuring the images have GPS metadata in their EXIF data. Enter a name for the output KMZ file and click the "Generate KMZ" button. Once processing is complete, use the download button to save the KMZ file to your computer. Finally, open Google Earth and import the downloaded KMZ file to view the images on the map.

## File Structure

The project contains the following files:

| File | Description |
|------|-------------|
| `app.py` | Main Streamlit application |
| `requirements.txt` | Python dependencies |
| `Fan.png` | Custom fan icon for Google Earth overlays |
| `Construct_Solutions_Logo_HALF.png` | Company logo |
| `README.md` | This documentation file |

## Requirements

Images must be in JPEG or PNG format and contain GPS metadata (latitude and longitude) in their EXIF data. Images taken with smartphones or GPS-enabled cameras typically include this data automatically.

## Dependencies

The application requires the following Python packages: streamlit, simplekml, Pillow, and requests. These are automatically installed when you run `pip install -r requirements.txt`.

## Company Information

This application is developed by **Construct Solutions**. For more information about our services, please visit our website or contact us directly.
