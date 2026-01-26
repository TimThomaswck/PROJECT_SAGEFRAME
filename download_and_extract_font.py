
import requests
import zipfile
import os

font_url = "https://fonts.google.com/download?family=Space+Grotesk"
download_path = "sageframe_desktop/app/resources/fonts/SpaceGrotesk.zip"
extract_path = "sageframe_desktop/app/resources/fonts"

os.makedirs(extract_path, exist_ok=True)

print(f"Downloading font from {font_url} to {download_path}...")
try:
    response = requests.get(font_url, stream=True)
    response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
    with open(download_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Download complete.")

    print(f"Extracting font to {extract_path}...")
    with zipfile.ZipFile(download_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    print("Extraction complete.")

except requests.exceptions.RequestException as e:
    print(f"Error during download: {e}")
except zipfile.BadZipFile as e:
    print(f"Error unzipping file: {e}. The downloaded file might be corrupt.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    # Clean up the zip file after extraction
    if os.path.exists(download_path):
        os.remove(download_path)
        print(f"Removed temporary zip file: {download_path}")
