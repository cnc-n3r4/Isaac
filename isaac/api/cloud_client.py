"""CloudClient - HTTP wrapper for GoDaddy session sync API."""

import requests
from typing import Optional


class CloudUnavailableError(Exception):
    """Raised when cloud API is unreachable."""


class CloudClient:
    """HTTP client for syncing Isaac session data to GoDaddy cloud API.
    
    All methods return False/None on errors (never raise exceptions).
    This ensures cloud failures don't crash Isaac.
    """
    
    def __init__(self, api_url: str, api_key: str, user_id: str):
        """Initialize CloudClient.
        
        Args:
            api_url: Base URL of GoDaddy API (e.g., https://n3r4.xyz/isaac/api)
            api_key: Authentication key for API
            user_id: Unique user identifier (e.g., "ndemi")
        """
        self.api_url = api_url.rstrip('/')  # Remove trailing slash
        self.api_key = api_key
        self.user_id = user_id
        self.timeout = 5  # seconds
    
    def health_check(self) -> bool:
        """Check if GoDaddy API is reachable.
        
        Returns:
            True if API responds with 200 OK, False otherwise
        """
        try:
            url = f"{self.api_url}/health_check.php"
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('status') == 'online'
            else:
                return False
                
        except Exception:
            # Network error, timeout, or malformed response
            return False
    
    def save_session_file(self, filename: str, data: dict) -> bool:
        """Save session file to cloud.
        
        Args:
            filename: Name of file (e.g., "preferences.json", "command_history.json")
            data: Dictionary to save
            
        Returns:
            True if saved successfully, False on error
        """
        try:
            url = f"{self.api_url}/save_session.php"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'user_id': self.user_id,
                'filename': filename,
                'data': data
            }
            
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
            else:
                return False
                
        except Exception:
            # Network error, timeout, or malformed response
            return False
    
    def get_session_file(self, filename: str) -> Optional[dict]:
        """Retrieve session file from cloud.
        
        Args:
            filename: Name of file to retrieve
            
        Returns:
            Dictionary if found, None if not found or on error
        """
        try:
            url = f"{self.api_url}/get_session.php"
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }
            params = {
                'user_id': self.user_id,
                'filename': filename
            }
            
            response = requests.get(
                url, 
                headers=headers, 
                params=params, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('data')
            
            # Not found or error
            return None
                
        except Exception:
            # Network error, timeout, or malformed response
            return None
    
    def is_available(self) -> bool:
        """Check if cloud sync is currently available.

        Wrapper around health_check() for semantic clarity.

        Returns:
            True if cloud API is reachable, False otherwise
        """
        return self.health_check()

    def route_command(self, device_alias: str, command: str) -> bool:
        """Route command to target device via cloud.

        Args:
            device_alias: Target device identifier (e.g., "laptop2")
            command: Command to execute on target device

        Returns:
            True if routed successfully, False on error
        """
        try:
            url = f"{self.api_url}/route_command.php"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'user_id': self.user_id,
                'target_device': device_alias,
                'command': command
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
            else:
                return False

        except Exception:
            return False

    def execute_cloud_meta(self, command: str) -> bool:
        """Execute cloud-dependent meta-command.

        Args:
            command: Meta-command that requires cloud (e.g., "/sync-history")

        Returns:
            True if executed successfully, False on error
        """
        try:
            url = f"{self.api_url}/execute_meta.php"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'user_id': self.user_id,
                'command': command
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
            else:
                return False

        except Exception:
            return False

    def log_command_history(self, command: str) -> bool:
        """Log command to cloud history for roaming.

        Args:
            command: Shell command to log

        Returns:
            True if logged successfully, False on error
        """
        try:
            url = f"{self.api_url}/log_command.php"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'user_id': self.user_id,
                'command': command,
                'timestamp': None  # Let server set timestamp
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
            else:
                return False

        except Exception:
            return False