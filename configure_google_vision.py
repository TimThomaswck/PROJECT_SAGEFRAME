#!/usr/bin/env python
"""Configure Google Vision API key for document extraction."""

import keyring
import getpass

def configure_google_vision():
    """Securely store Google Vision API key."""
    print("\n" + "="*70)
    print("Google Vision API Key Configuration")
    print("="*70)
    
    # Check if key already exists
    existing_key = keyring.get_password("sageframe_file_ingestion", "google_vision")
    if existing_key:
        print(f"✓ Existing key found: {existing_key[:10]}...")
        change = input("\nDo you want to replace it? (y/n): ").lower()
        if change != 'y':
            print("Configuration cancelled.")
            return
    
    # Get new API key
    print("\nEnter your Google Vision API key:")
    print("(Get one from: https://console.cloud.google.com/apis/credentials)")
    api_key = getpass.getpass("API Key: ").strip()
    
    if not api_key:
        print("✗ No API key provided. Exiting.")
        return
    
    # Store in keyring
    try:
        keyring.set_password("sageframe_file_ingestion", "google_vision", api_key)
        print("\n✓ Google Vision API key configured successfully!")
        print(f"  Service: sageframe_file_ingestion")
        print(f"  Key name: google_vision")
        print(f"  Key (masked): {api_key[:10]}...{api_key[-5:]}")
    except Exception as e:
        print(f"\n✗ Error storing key: {e}")
        return
    
    # Verify it was stored
    stored_key = keyring.get_password("sageframe_file_ingestion", "google_vision")
    if stored_key == api_key:
        print("\n✓ Verification successful - key is ready to use!")
    else:
        print("\n✗ Verification failed - there may be an issue with keyring")

if __name__ == "__main__":
    configure_google_vision()
