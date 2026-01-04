"""
Microsoft Graph Authentication Configuration
Uses MSAL with device code flow for local development
"""

import os
import json
from pathlib import Path
from typing import Optional
from msal import PublicClientApplication

# Microsoft Graph API scopes (read-only)
GRAPH_SCOPES = [
    "User.Read",
    "Calendars.Read",
    "Mail.Read",
    "Tasks.Read",
]

# Token cache file
TOKEN_CACHE_FILE = Path(__file__).parent / ".token_cache.json"


class GraphAuthManager:
    """Manages Microsoft Graph authentication using device code flow."""
    
    def __init__(self):
        self.client_id = os.getenv("M365_CLIENT_ID", "")
        self.tenant_id = os.getenv("M365_TENANT_ID", "common")
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        
        if not self.client_id:
            raise ValueError("M365_CLIENT_ID environment variable is required")
        
        self._app = PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
        )
        self._load_token_cache()
    
    def _load_token_cache(self):
        """Load cached tokens from file."""
        if TOKEN_CACHE_FILE.exists():
            try:
                self._app.token_cache.deserialize(TOKEN_CACHE_FILE.read_text())
            except Exception:
                pass
    
    def _save_token_cache(self):
        """Save tokens to cache file."""
        try:
            TOKEN_CACHE_FILE.write_text(self._app.token_cache.serialize())
        except Exception:
            pass
    
    def get_access_token(self) -> Optional[str]:
        """
        Get an access token for Microsoft Graph.
        Uses cached token if available, otherwise initiates device code flow.
        """
        accounts = self._app.get_accounts()
        
        # Try to get token silently from cache
        if accounts:
            result = self._app.acquire_token_silent(GRAPH_SCOPES, account=accounts[0])
            if result and "access_token" in result:
                self._save_token_cache()
                return result["access_token"]
        
        # Initiate device code flow
        flow = self._app.initiate_device_flow(scopes=GRAPH_SCOPES)
        
        if "user_code" not in flow:
            raise Exception(f"Failed to create device flow: {flow.get('error_description', 'Unknown error')}")
        
        print("\n" + "=" * 60)
        print("AUTHENTICATION REQUIRED")
        print("=" * 60)
        print(f"\nTo sign in, open a browser and go to:")
        print(f"  {flow['verification_uri']}")
        print(f"\nEnter the code: {flow['user_code']}")
        print("\nWaiting for authentication...")
        print("=" * 60 + "\n")
        
        result = self._app.acquire_token_by_device_flow(flow)
        
        if "access_token" in result:
            self._save_token_cache()
            print("✓ Authentication successful!\n")
            return result["access_token"]
        else:
            error = result.get("error_description", "Unknown error")
            raise Exception(f"Authentication failed: {error}")


# Singleton instance
_auth_manager: Optional[GraphAuthManager] = None


def get_auth_manager() -> GraphAuthManager:
    """Get the singleton auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = GraphAuthManager()
    return _auth_manager


def get_access_token() -> str:
    """Convenience function to get access token."""
    return get_auth_manager().get_access_token()
