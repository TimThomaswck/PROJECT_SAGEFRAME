"""Google OAuth 2.0 client for calendar authentication.

This module implements OAuth 2.0 authentication flow for Google Calendar using
the official Google Auth library. Tokens are stored securely in system keyring.
"""

import os
import json
from typing import Optional, Dict, Any
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


# OAuth 2.0 scopes for Google Calendar API
GOOGLE_CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar",  # Full calendar access
    "https://www.googleapis.com/auth/calendar.events",  # Events read/write
]


class GoogleOAuthClient:
    """Google OAuth 2.0 client for calendar authentication.
    
    Handles OAuth flow, token exchange, and token refresh for Google Calendar API.
    Uses InstalledAppFlow for desktop app authentication (opens browser for consent).
    """
    
    def __init__(self, client_secrets_file: Optional[str] = None):
        """Initialize OAuth client.
        
        Args:
            client_secrets_file: Path to Google OAuth client secrets JSON file.
                                If None, looks for credentials.json in user's config dir.
        """
        self.scopes = GOOGLE_CALENDAR_SCOPES
        
        # Default client secrets location
        if client_secrets_file is None:
            config_dir = Path.home() / ".sageframe" / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            client_secrets_file = str(config_dir / "google_oauth_credentials.json")
        
        self.client_secrets_file = client_secrets_file
    
    def has_client_secrets(self) -> bool:
        """Check if OAuth client secrets file exists.
        
        Returns:
            True if client secrets file exists, False otherwise
        """
        return os.path.exists(self.client_secrets_file)
    
    def save_client_secrets(self, client_config: Dict[str, Any]):
        """Save OAuth client secrets to file.
        
        Args:
            client_config: OAuth client configuration (downloaded from Google Cloud Console)
        """
        os.makedirs(os.path.dirname(self.client_secrets_file), exist_ok=True)
        with open(self.client_secrets_file, 'w') as f:
            json.dump(client_config, f, indent=2)
    
    def initiate_oauth_flow(self) -> Credentials:
        """Start OAuth 2.0 flow and obtain credentials.
        
        Opens browser for user to grant calendar access. User must authenticate
        with their Google account and grant permissions.
        
        Returns:
            Google OAuth credentials with access and refresh tokens
        
        Raises:
            FileNotFoundError: If client secrets file doesn't exist
            ValueError: If OAuth flow fails
        """
        if not self.has_client_secrets():
            raise FileNotFoundError(
                f"OAuth client secrets not found at {self.client_secrets_file}. "
                "Please configure Google OAuth credentials in Settings."
            )
        
        # Create OAuth flow from client secrets
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secrets_file,
            scopes=self.scopes
        )
        
        # Run local server for OAuth callback (opens browser)
        # Port 0 means use any available port
        creds = flow.run_local_server(port=0)
        
        return creds
    
    def refresh_credentials(self, refresh_token: str) -> Credentials:
        """Refresh access token using refresh token.
        
        Args:
            refresh_token: OAuth refresh token
        
        Returns:
            New credentials with refreshed access token
        
        Raises:
            Exception: If token refresh fails (e.g., refresh token revoked)
        """
        # Load client secrets to get client_id and client_secret
        with open(self.client_secrets_file, 'r') as f:
            client_config = json.load(f)
        
        # Extract client info (handle both "installed" and "web" app types)
        if "installed" in client_config:
            client_info = client_config["installed"]
        elif "web" in client_config:
            client_info = client_config["web"]
        else:
            raise ValueError("Invalid client secrets format")
        
        # Create credentials object with refresh token
        creds = Credentials(
            token=None,  # Will be populated after refresh
            refresh_token=refresh_token,
            token_uri=client_info.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=client_info["client_id"],
            client_secret=client_info["client_secret"],
            scopes=self.scopes
        )
        
        # Refresh the access token
        creds.refresh(Request())
        
        return creds
    
    def credentials_from_tokens(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expiry: Optional[str] = None
    ) -> Credentials:
        """Create credentials object from stored tokens.
        
        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token (optional)
            token_expiry: Token expiration timestamp (ISO 8601)
        
        Returns:
            Google OAuth credentials object
        """
        # Load client secrets for client_id and client_secret
        with open(self.client_secrets_file, 'r') as f:
            client_config = json.load(f)
        
        if "installed" in client_config:
            client_info = client_config["installed"]
        elif "web" in client_config:
            client_info = client_config["web"]
        else:
            raise ValueError("Invalid client secrets format")
        
        # Parse expiry timestamp if provided
        expiry = None
        if token_expiry:
            from datetime import datetime
            expiry = datetime.fromisoformat(token_expiry.replace('Z', '+00:00'))
        
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=client_info.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=client_info["client_id"],
            client_secret=client_info["client_secret"],
            scopes=self.scopes,
            expiry=expiry
        )
        
        return creds
    
    def is_token_expired(self, creds: Credentials) -> bool:
        """Check if credentials are expired.
        
        Args:
            creds: Google OAuth credentials
        
        Returns:
            True if token is expired, False otherwise
        """
        return not creds.valid
    
    def auto_refresh_if_needed(self, creds: Credentials) -> Credentials:
        """Automatically refresh credentials if expired.
        
        Args:
            creds: Google OAuth credentials
        
        Returns:
            Refreshed credentials (or original if still valid)
        """
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds
