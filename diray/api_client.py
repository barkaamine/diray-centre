"""
API Client for Système de Calcul (Main Application)
===================================================

This module provides a client to communicate with the Système de Calcul API
for authentication and data synchronization.

The Diray Centre (vitrine site) uses this client to:
1. Authenticate students via the main application's API
2. Fetch student data (formations, schedule, etc.)
3. Sync data between the two applications
"""

import requests
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class SystemeCalculAPIError(Exception):
    """Exception raised when API call fails"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class SystemeCalculClient:
    """
    Client for communicating with Système de Calcul API

    Usage:
        client = SystemeCalculClient()

        # Authenticate a student
        result = client.authenticate_student('student@email.com', 'password')
        if result['success']:
            student = result['student']
            token = result['token']

        # Fetch student profile (requires token)
        profile = client.get_student_profile(token)
    """

    def __init__(self):
        """Initialize the API client with settings"""
        self.base_url = getattr(settings, 'SYSTEME_CALCUL_API_URL', None)
        self.api_key = getattr(settings, 'SYSTEME_CALCUL_API_KEY', None)
        self.timeout = getattr(settings, 'SYSTEME_CALCUL_API_TIMEOUT', 30)

        if not self.base_url:
            logger.warning("SYSTEME_CALCUL_API_URL not configured in settings")
        if not self.api_key:
            logger.warning("SYSTEME_CALCUL_API_KEY not configured in settings")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        token: Optional[str] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to the API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data (for POST/PUT)
            token: JWT token for authentication
            params: Query parameters

        Returns:
            API response as dictionary

        Raises:
            SystemeCalculAPIError: If the request fails
        """
        if not self.base_url:
            raise SystemeCalculAPIError("API URL not configured")

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                json=data,
                headers=headers,
                params=params,
                timeout=self.timeout
            )

            # Try to parse JSON response
            try:
                response_data = response.json()
            except ValueError:
                response_data = {'raw': response.text}

            # Check for errors
            if not response.ok:
                error_message = response_data.get('error', f'HTTP {response.status_code}')
                raise SystemeCalculAPIError(
                    message=error_message,
                    status_code=response.status_code,
                    response_data=response_data
                )

            return response_data

        except requests.exceptions.Timeout:
            raise SystemeCalculAPIError("Request timeout - API server not responding")
        except requests.exceptions.ConnectionError:
            raise SystemeCalculAPIError("Connection error - Cannot reach API server")
        except requests.exceptions.RequestException as e:
            raise SystemeCalculAPIError(f"Request failed: {str(e)}")

    def authenticate_student(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a student via the external login endpoint

        Args:
            email: Student's email address
            password: Student's password

        Returns:
            Dictionary containing:
            - success: bool
            - student: dict with student info (if successful)
            - token: JWT token (if successful)
            - error: error message (if failed)
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'API key not configured'
            }

        try:
            response = self._make_request(
                method='POST',
                endpoint='/auth/external-login',
                data={
                    'email': email,
                    'password': password,
                    'app_key': self.api_key
                }
            )

            return {
                'success': True,
                'student': response.get('student'),
                'token': response.get('token'),
                'expires_in': response.get('expiresIn', '24h')
            }

        except SystemeCalculAPIError as e:
            logger.error(f"Authentication failed for {email}: {e.message}")
            return {
                'success': False,
                'error': e.message
            }

    def get_student_profile(self, token: str) -> Dict[str, Any]:
        """
        Get the authenticated student's profile with formations and schedule

        Args:
            token: JWT token from authentication

        Returns:
            Dictionary containing student profile, formations, and schedule
        """
        cache_key = f"student_profile_{token[:20]}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        try:
            response = self._make_request(
                method='GET',
                endpoint='/students/me/profile',
                token=token
            )

            # Cache for 5 minutes
            cache.set(cache_key, response, 300)

            return response

        except SystemeCalculAPIError as e:
            logger.error(f"Failed to get student profile: {e.message}")
            return {
                'success': False,
                'error': e.message
            }

    def get_student_formations(self, student_id: int, token: str) -> Dict[str, Any]:
        """
        Get formations for a specific student

        Args:
            student_id: Student ID
            token: JWT token

        Returns:
            List of formations the student is enrolled in
        """
        try:
            response = self._make_request(
                method='GET',
                endpoint=f'/students/{student_id}/formations',
                token=token
            )
            return response
        except SystemeCalculAPIError as e:
            logger.error(f"Failed to get formations for student {student_id}: {e.message}")
            return {'success': False, 'error': e.message, 'formations': []}

    def get_student_schedule(self, student_id: int, token: str) -> Dict[str, Any]:
        """
        Get schedule for a specific student

        Args:
            student_id: Student ID
            token: JWT token

        Returns:
            Student's upcoming schedule
        """
        try:
            response = self._make_request(
                method='GET',
                endpoint=f'/students/{student_id}/schedule',
                token=token
            )
            return response
        except SystemeCalculAPIError as e:
            logger.error(f"Failed to get schedule for student {student_id}: {e.message}")
            return {'success': False, 'error': e.message, 'schedule': []}

    def verify_token(self, token: str) -> bool:
        """
        Verify if a JWT token is still valid

        Args:
            token: JWT token to verify

        Returns:
            True if token is valid, False otherwise
        """
        try:
            self._make_request(
                method='GET',
                endpoint='/auth/me',
                token=token
            )
            return True
        except SystemeCalculAPIError:
            return False

    def refresh_token(self, token: str) -> Optional[str]:
        """
        Refresh an existing JWT token

        Args:
            token: Current JWT token

        Returns:
            New JWT token or None if refresh failed
        """
        try:
            response = self._make_request(
                method='POST',
                endpoint='/auth/refresh',
                token=token
            )
            return response.get('token')
        except SystemeCalculAPIError as e:
            logger.error(f"Failed to refresh token: {e.message}")
            return None


# Singleton instance for easy access
_client_instance = None

def get_api_client() -> SystemeCalculClient:
    """
    Get a singleton instance of the API client

    Returns:
        SystemeCalculClient instance
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = SystemeCalculClient()
    return _client_instance
