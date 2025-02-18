"""Simple Database Connection Implementation for Pangolin SDK."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPDigestAuth
from requests.exceptions import ConnectionError, RequestException, Timeout

from pangolin_sdk.configs.api import APIConfig, AuthMethod
from pangolin_sdk.connections.base import BaseConnection
from pangolin_sdk.exceptions import APIConnectionError


class APIConnection(BaseConnection):
    """Implementation of API connection handling.

    Attributes:
        config (APIConfig): Configuration for API connection.
        _session (Optional[requests.Session]): HTTP session for API requests.
        _last_request_time (Optional[datetime]): Timestamp of last request.
        _is_connected (bool): Flag indicating connection status.
        _response (Optional[requests.Response]): Last API response.
    """

    def __init__(self, config: APIConfig):
        """
        Initialize API connection.

        Args:
            config (APIConfig): Configuration for API connection.
        """
        super().__init__(config)
        self.config = config
        self._session: Optional[requests.Session] = None
        self._last_request_time: Optional[datetime] = None
        self._is_connected: bool = False
        self._response: Optional[requests.Response] = None
        self._logger = logging.getLogger(__name__)

    def _connect_impl(self) -> requests.Session:
        """
        Implements connection logic by:
        1. Creating a new session
        2. Setting up headers and auth
        3. Testing connection with HEAD request
        4. Returning success status

        Returns:
            requests.Session: Configured requests session.

        Raises:
            APIConnectionError: If connection fails.
        """
        try:
            # 1. Create new session
            self._session = requests.Session()

            # 2. Setup headers and authentication
            # First, add default headers
            self._session.headers.update(self.config.default_headers)
            if "headers" in self.config.options:
                self._session.headers.update(self.config.options["headers"])

            # Then, add authentication headers
            self._setup_authentication()

            # 3. Test connection with HEAD request
            self._response = self._session.head(
                self.config.host, timeout=self.config.timeout
            )

            # 4. Check response and store session if successful
            return self._validate_connection()

        except (RequestException, ConnectionError, Timeout) as e:
            error = APIConnectionError(
                message=f"Connection test failed: {e}",
                status_code=getattr(self._response, "status_code", None),
            )
            self._logger.error("API connection error: %s", str(error))
            raise error from e

    def _setup_authentication(self) -> None:
        """
        Set up authentication for the API session.
        """
        if self.config.auth_method == AuthMethod.DIGEST:
            self._session.auth = HTTPDigestAuth(
                self.config.username, self.config.password
            )

        auth_headers = self.config.get_auth_headers()
        if auth_headers:
            self._session.headers.update(auth_headers)

    def _validate_connection(self) -> requests.Session:
        """
        Validate the connection based on response status.

        Returns:
            requests.Session: Configured session if connection is successful.

        Raises:
            APIConnectionError: If connection validation fails.
        """
        if self._response is None:
            raise APIConnectionError(
                message="No response received during connection test",
                status_code=None
            )

        if self._response.status_code in [200, 201, 204]:
            self._is_connected = True
            self._last_result = {
                "status_code": self._response.status_code,
                "headers": dict(self._response.headers),
                "connection_time": datetime.now(),
            }
            return self._session

        error = APIConnectionError(
            message=f"Connection test failed with status {self._response.status_code}",
            status_code=self._response.status_code,
        )
        raise error

    def _disconnect_impl(self) -> None:
        """
        Implements disconnection logic.

        Raises:
            ConnectionError: If disconnection fails.
        """
        try:
            # Cancel any pending requests
            if self._session:
                self._session.close()

            # Clear session and results
            self._session = None
            self._last_request_time = None
            self._retry_count = 0
            self._is_connected = False

        except Exception as e:
            error_msg = f"Error during disconnection: {e}"
            self._logger.error(error_msg)
            raise ConnectionError(error_msg) from e

    def _execute_impl(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute an API request.

        Args:
            *args: Positional arguments (unused).
            **kwargs: Keyword arguments for request configuration.
                Expected keys:
                - method (str, optional): HTTP method (default: 'GET')
                - endpoint (str, optional): API endpoint
                - data (Any, optional): Request payload
                - params (Dict, optional): Query parameters
                - headers (Dict, optional): Additional headers

        Returns:
            Dict[str, Any]: Request result with response details.

        Raises:
            APIConnectionError: If request fails.
        """
        try:
            # Prepare request parameters with defaults
            method = kwargs.get("method", "GET").upper()
            endpoint = kwargs.get("endpoint", "")
            data = kwargs.get("data")
            params = kwargs.get("params")
            headers = kwargs.get("headers")

            # Ensure connection
            if self._session is None:
                self.connect()

            # Execute request
            return self._perform_request(method, endpoint, data, params, headers)

        except Exception as e:
            self._last_error = e
            self._logger.error("API request failed: %s", str(e))
            raise

    def _perform_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Perform the actual API request.

        Args:
            method: HTTP method.
            endpoint: API endpoint.
            data: Request payload.
            params: Query parameters.
            headers: Additional headers.

        Returns:
            Dict with request result details.

        Raises:
            APIConnectionError: If request fails.
        """
        url = self.config.get_full_url(endpoint)
        start_time = datetime.now()

        self._response = self._session.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=headers,
            timeout=self.config.timeout,
        )
        end_time = datetime.now()

        # Check for HTTP error status
        if self._response.status_code >= 400:
            raise APIConnectionError(
                message=f"API request failed with status {self._response.status_code}",
                status_code=self._response.status_code,
            )

        # Prepare result dictionary
        result = {
            "status_code": self._response.status_code,
            "headers": dict(self._response.headers),
            "elapsed_ms": (end_time - start_time).total_seconds() * 1000,
            "url": self._response.url,
            "method": method,
        }

        # Parse response content
        try:
            result["data"] = self._response.json()
        except ValueError:
            result["data"] = self._response.text

        # Finalize request tracking
        self._response.raise_for_status()
        self._last_result = result
        self._last_error = None
        self._last_request_time = datetime.now()

        return result
