#!/usr/bin/env python
"""Test Google Vision API directly."""

import sys
import asyncio
import keyring

# Add the app to path
sys.path.insert(0, 'sageframe_desktop')

from sageframe_desktop.app.modules.file_ingestion.extraction.ocr_clients import GoogleVisionClient


async def test_vision_api(image_path: str):
    """Test Google Vision API with an image."""
    print("\n" + "="*70)
    print("Google Vision API Test")
    print("="*70)
    
    # Get API key
    print("\n1. Retrieving API key from keyring...")
    api_key = keyring.get_password("sageframe_file_ingestion", "google_vision")
    
    if not api_key:
        print("✗ No API key found in keyring!")
        print("  Run the configure_google_vision.py script first.")
        return
    
    print(f"✓ API key found: {api_key[:10]}...{api_key[-5:]}")
    
    # Test image file
    print(f"\n2. Testing image: {image_path}")
    import os
    if not os.path.exists(image_path):
        print(f"✗ Image file not found: {image_path}")
        return
    
    file_size = os.path.getsize(image_path) / 1024
    print(f"✓ Image exists ({file_size:.1f} KB)")
    
    # Call Vision API
    print("\n3. Calling Google Vision API...")
    try:
        async with GoogleVisionClient(api_key) as client:
            text = await client.extract_text(image_path)
        
        print("\n" + "="*70)
        print("✓ SUCCESS! Text extracted:")
        print("="*70)
        print(text[:500] if text else "(empty)")
        print("="*70)
        print(f"\nTotal characters extracted: {len(text) if text else 0}")
        
    except Exception as e:
        print("\n" + "="*70)
        print("✗ ERROR:")
        print("="*70)
        print(f"{type(e).__name__}: {e}")
        print("\nFull traceback:")
        import traceback
        traceback.print_exc()
        print("="*70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_google_vision.py <image_path>")
        print("\nExample:")
        print('  python test_google_vision.py "C:\\Users\\LEGION\\Downloads\\bill.jpg"')
        sys.exit(1)
    
    image_path = sys.argv[1]
    asyncio.run(test_vision_api(image_path))
