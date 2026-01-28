"""OCR clients for external providers.

Includes Google Vision REST client for TEXT_DETECTION.
"""

import base64
from typing import Optional, Dict, Any

import httpx


class GoogleVisionClient:
    def __init__(self, api_key: str, timeout: float = 15.0):
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def extract_text(self, file_path: str) -> Optional[str]:
        """Run TEXT_DETECTION on an image file and return concatenated text."""
        if not self._client:
            raise RuntimeError("Client not initialized; use 'async with GoogleVisionClient(...) as client'")

        # Load image
        with open(file_path, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode("ascii")

        url = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"
        payload = {
            "requests": [
                {
                    "image": {"content": content_b64},
                    "features": [{"type": "TEXT_DETECTION"}],
                }
            ]
        }

        resp = await self._client.post(url, json=payload)
        
        # Capture response details for debugging
        if resp.status_code != 200:
            print(f"[GoogleVision] HTTP {resp.status_code} error")
            print(f"[GoogleVision] Response body: {resp.text}")
        
        resp.raise_for_status()
        data = resp.json()
        try:
            annotations = data["responses"][0].get("textAnnotations", [])
            if not annotations:
                return None
            # First entry usually contains full text
            return annotations[0].get("description")
        except Exception:
            return None
