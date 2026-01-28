"""Cloudmersive OCR client for text extraction from images."""

from typing import Optional
import requests
import keyring


class CloudmersiveOCRClient:
    """Cloudmersive-based OCR client for document text extraction."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Cloudmersive OCR client.
        
        Args:
            api_key: Cloudmersive API key (if None, retrieves from keyring)
        """
        self.api_key = api_key or self._get_api_key()
        self.api_url = "https://api.cloudmersive.com/ocr/photo/toText"
        
        if not self.api_key:
            raise ValueError("Cloudmersive API key not configured. Please set it in keyring or pass it directly.")
    
    def _get_api_key(self) -> Optional[str]:
        """Get Cloudmersive API key from keyring."""
        try:
            return keyring.get_password("sageframe_file_ingestion", "cloudmersive")
        except Exception:
            return None
    
    def extract_text(self, file_path: str) -> Optional[str]:
        """Extract text from an image file using Cloudmersive API.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            print(f"[Cloudmersive] Extracting text from: {file_path}")
            
            # Prepare request
            headers = {"Apikey": self.api_key}
            
            with open(file_path, "rb") as f:
                files = {"imageFile": f}
                
                # Call Cloudmersive API
                response = requests.post(self.api_url, headers=headers, files=files)
            
            # Check response status
            if response.status_code != 200:
                print(f"[Cloudmersive] API error {response.status_code}")
                print(f"[Cloudmersive] Response: {response.text}")
                return None
            
            data = response.json()
            
            # Extract text from response
            if data.get("IsErrored"):
                print(f"[Cloudmersive] OCR error: {data.get('ErrorMessage', 'Unknown error')}")
                return None
            
            text = data.get("OCRText", "")
            
            if text:
                print(f"[Cloudmersive] Successfully extracted {len(text)} characters")
                return text
            else:
                print(f"[Cloudmersive] No text detected in image")
                return None
        
        except Exception as e:
            print(f"[Cloudmersive] Error during text extraction: {e}")
            import traceback
            traceback.print_exc()
            return None

