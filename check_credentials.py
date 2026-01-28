#!/usr/bin/env python
"""Check Google credentials type and compatibility."""

import json
import os

credentials_path = os.path.expanduser("~/.sageframe/client_secret.json")

if not os.path.exists(credentials_path):
    print("✗ Credentials file not found at:", credentials_path)
    exit(1)

try:
    with open(credentials_path, 'r') as f:
        creds = json.load(f)
    
    print("\n" + "="*70)
    print("Google Credentials Analysis")
    print("="*70)
    
    # Determine credential type
    if "type" in creds:
        cred_type = creds["type"]
        print(f"\n✓ Credential Type: {cred_type}")
        
        if cred_type == "service_account":
            print("\n✓ Service Account Key detected")
            print("  This will work with:")
            print("  - Google Vision API ✓")
            print("  - Gemini API ✓")
            print("  - Other Google APIs ✓")
            print("\n  To use with Google Vision:")
            print("  1. Store the JSON file path or client email in keyring")
            print("  2. Or convert to API Key at Google Cloud Console")
            
        elif cred_type == "oauth2":
            print("\n✓ OAuth2 Credentials detected")
            print("  This is typically for user-facing applications")
            print("  May need conversion for service-to-service use")
        else:
            print(f"\n⚠ Unknown credential type: {cred_type}")
    else:
        print("\n⚠ No 'type' field found")
        print("  Keys present:", list(creds.keys()))
    
    # Show other relevant fields
    if "project_id" in creds:
        print(f"\n✓ Project ID: {creds['project_id']}")
    
    if "client_email" in creds:
        print(f"✓ Service Account Email: {creds['client_email']}")

except json.JSONDecodeError as e:
    print(f"✗ Invalid JSON: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
