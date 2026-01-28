"""Cloudmersive OCR client for text extraction from images."""

from typing import Optional
import requests


class CloudmersiveOCRClient:
    """Cloudmersive-based OCR client for document text extraction."""
    
    API_URL = "https://api.cloudmersive.com/ocr/photo/toText"
    
    def __init__(self, api_key: str):
        """Initialize Cloudmersive OCR client.
        
        Args:
            api_key: Cloudmersive API key
        """
        self.api_key = api_key
        if not api_key:
            raise ValueError("Cloudmersive API key is required")
    
    def extract_text(self, file_path: str) -> Optional[str]:
        """Extract text from an image file.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            print(f"[Cloudmersive] Extracting text from: {file_path}")
            
            headers = {"Apikey": self.api_key}
            
            with open(file_path, "rb") as f:
                files = {"imageFile": f}
                response = requests.post(
                    self.API_URL,
                    headers=headers,
                    files=files,
                    timeout=30
                )
            
            if response.status_code != 200:
                print(f"[Cloudmersive] HTTP {response.status_code}")
                print(f"[Cloudmersive] Response: {response.text}")
                response.raise_for_status()
            
            data = response.json()
            
            # Check for success
            if not data.get("Successful"):
                error_msg = data.get("ErrorMessage", "Unknown error")
                print(f"[Cloudmersive] API error: {error_msg}")
                return None
            
            # Extract text
            full_text = data.get("OCRText", "")
            
            if not full_text:
                print(f"[Cloudmersive] No text detected in image")
                return None
            
            print(f"[Cloudmersive] Successfully extracted {len(full_text)} characters")
            return full_text
        
        except Exception as e:
            print(f"[Cloudmersive] Error during text extraction: {e}")
            import traceback
            traceback.print_exc()
            return None
