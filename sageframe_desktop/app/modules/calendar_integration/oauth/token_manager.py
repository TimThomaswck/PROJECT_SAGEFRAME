"""Token manager for secure OAuth token storage.

This module handles secure storage and retrieval of OAuth tokens using
the system keyring (Windows Credential Manager on Windows).
"""

import keyring
from typing import Optional, Tuple
from datetime import datetime, timezone


class TokenManager:
    """Manages secure storage of OAuth tokens in system keyring.
    
    Tokens are stored in Windows Credential Manager (or platform equivalent)
    rather than in the database for enhanced security.
    """
    
    SERVICE_NAME = "sageframe_calendar"
    
    def __init__(self):
        """Initialize token manager."""
        pass
    
    def store_tokens(
        self,
        connection_id: int,
        access_token: str,
        refresh_token: str,
        expires_at: Optional[datetime] = None
    ):
        """Store OAuth tokens securely in keyring.
        
        Args:
            connection_id: Calendar connection ID
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_at: Token expiration timestamp (optional)
        """
        # Store access token
        keyring.set_password(
            self.SERVICE_NAME,
            f"connection_{connection_id}_access",
            access_token
        )
        
        # Store refresh token
        keyring.set_password(
            self.SERVICE_NAME,
            f"connection_{connection_id}_refresh",
            refresh_token
        )
        
        # Store expiry timestamp if provided
        if expires_at:
            expiry_str = expires_at.isoformat()
            keyring.set_password(
                self.SERVICE_NAME,
                f"connection_{connection_id}_expiry",
                expiry_str
            )
    
    def get_access_token(self, connection_id: int) -> Optional[str]:
        """Retrieve access token from keyring.
        
        Args:
            connection_id: Calendar connection ID
        
        Returns:
            Access token or None if not found
        """
        return keyring.get_password(
            self.SERVICE_NAME,
            f"connection_{connection_id}_access"
        )
    
    def get_refresh_token(self, connection_id: int) -> Optional[str]:
        """Retrieve refresh token from keyring.
        
        Args:
            connection_id: Calendar connection ID
        
        Returns:
            Refresh token or None if not found
        """
        return keyring.get_password(
            self.SERVICE_NAME,
            f"connection_{connection_id}_refresh"
        )
    
    def get_token_expiry(self, connection_id: int) -> Optional[datetime]:
        """Retrieve token expiration timestamp from keyring.
        
        Args:
            connection_id: Calendar connection ID
        
        Returns:
            Expiration datetime or None if not found
        """
        expiry_str = keyring.get_password(
            self.SERVICE_NAME,
            f"connection_{connection_id}_expiry"
        )
        if expiry_str:
            return datetime.fromisoformat(expiry_str)
        return None
    
    def get_tokens(self, connection_id: int) -> Tuple[Optional[str], Optional[str], Optional[datetime]]:
        """Retrieve all tokens for a connection.
        
        Args:
            connection_id: Calendar connection ID
        
        Returns:
            Tuple of (access_token, refresh_token, expires_at)
        """
        access_token = self.get_access_token(connection_id)
        refresh_token = self.get_refresh_token(connection_id)
        expires_at = self.get_token_expiry(connection_id)
        return (access_token, refresh_token, expires_at)
    
    def update_access_token(self, connection_id: int, access_token: str, expires_at: datetime):
        """Update access token after refresh.
        
        Args:
            connection_id: Calendar connection ID
            access_token: New access token
            expires_at: New expiration timestamp
        """
        keyring.set_password(
            self.SERVICE_NAME,
            f"connection_{connection_id}_access",
            access_token
        )
        
        expiry_str = expires_at.isoformat()
        keyring.set_password(
            self.SERVICE_NAME,
            f"connection_{connection_id}_expiry",
            expiry_str
        )
    
    def delete_tokens(self, connection_id: int):
        """Delete all tokens for a connection.
        
        Args:
            connection_id: Calendar connection ID
        """
        try:
            keyring.delete_password(
                self.SERVICE_NAME,
                f"connection_{connection_id}_access"
            )
        except keyring.errors.PasswordDeleteError:
            pass
        
        try:
            keyring.delete_password(
                self.SERVICE_NAME,
                f"connection_{connection_id}_refresh"
            )
        except keyring.errors.PasswordDeleteError:
            pass
        
        try:
            keyring.delete_password(
                self.SERVICE_NAME,
                f"connection_{connection_id}_expiry"
            )
        except keyring.errors.PasswordDeleteError:
            pass
    
    def is_token_expired(self, connection_id: int) -> bool:
        """Check if access token is expired.
        
        Args:
            connection_id: Calendar connection ID
        
        Returns:
            True if expired or expiry not found, False if still valid
        """
        expires_at = self.get_token_expiry(connection_id)
        if not expires_at:
            return True  # No expiry means we should treat as expired
        
        now = datetime.now(timezone.utc)
        # Add 5-minute buffer to account for clock skew
        from datetime import timedelta
        return now >= (expires_at - timedelta(minutes=5))
