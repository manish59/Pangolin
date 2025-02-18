"""Simple Database Connection Implementation for Pangolin SDK."""

from datetime import datetime
from typing import Any, Dict

import requests
from requests.auth import HTTPDigestAuth
from requests.exceptions import ConnectionError, RequestException, Timeout

from pangolin_sdk.configs.api import APIConfig, AuthMethod
from pangolin_sdk.connections.base import BaseConnection
from pangolin_sdk.exceptions import APIConnectionError


class APIConnection(BaseConnection):
    """Implementation of API connection handling"""

    def __init__(self, config: APIConfig):
        super().__init__(config)
        self.config = config
        self._session = requests.Session()
        self._last_request_time = None
        self._is_connected = False
        self._response = None

    def _connect_impl(self) -> requests.Session:
        """
        Implements connection logic by:
        1. Creating a new session
        2. Setting up headers and auth
        3. Testing connection with HEAD request
        4. Returning success status
        """
        try:
            # 1. Create new session

            # 2. Setup headers and authentication
            # First, add default headers
            self._session.headers.update(self.config.default_headers)
            if "headers" in self.config.options:
                self._session.headers.update(self.config.options["headers"])

            # Then, add authentication headers
            if self.config.auth_method == AuthMethod.DIGEST:
                self._session.auth = HTTPDigestAuth(
                    self.config.username, self.config.password
                )
            auth_headers = self.config.get_auth_headers()
            if auth_headers:
                self._session.headers.update(auth_headers)

            # 3. Test connection with HEAD request
            self._response = self._session.head(
                self.config.host, timeout=self.config.timeout
            )

            # 4. Check response and store session if successful
            if self._response.status_code in [200, 201, 204]:
                self._is_connected = True
                self._last_result = {
                    "status_code": self._response.status_code,
                    "headers": dict(self._response.headers),
                    "connection_time": datetime.now(),
                }
                return self._session

            else:
                error = APIConnectionError(
                    message=f"Connection test failed with status {getattr(self._response, 'status_code', None)}",
                    status_code=getattr(self._response, "status_code", None),
                )
                raise error

        except (RequestException, ConnectionError, Timeout) as e:
            error = APIConnectionError(
                message=f"Connection test failed with status {e}",
                status_code=getattr(self._response, "status_code", None),
            )
            raise error

    def _disconnect_impl(self) -> None:
        """
        Implements disconnection logic
        """
        try:
            # Cancel any pending requests
            if self._session:
                self._session.close()

            # Clear session and results
            self._session = None
            self._last_request_time = None
            self._retry_count = 0

        except Exception as e:
            raise ConnectionError(f"Error during disconnection: {str(e)}")

    def _execute_impl(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute an API request
        """
        method = kwargs.get("method", "GET")
        endpoint = kwargs.get("endpoint", "")
        data = kwargs.get("data")
        params = kwargs.get("params")
        headers = kwargs.get("headers")
        try:
            # Prepare request
            if self._session is None:
                self.connect()
            url = self.config.get_full_url(endpoint)
            # Execute request
            start_time = datetime.now()
            self._response = self._session.request(
                method=method.upper(),
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.config.timeout,
            )
            end_time = datetime.now()
            if self._response.status_code >= 400:
                raise APIConnectionError(
                    message=f"API request failed with status {self._response.status_code}",
                    status_code=self._response.status_code,
                )
            else:
                # Prepare result
                result = {
                    "status_code": self._response.status_code,
                    "headers": dict(self._response.headers),
                    "elapsed_ms": (end_time - start_time).total_seconds() * 1000,
                    "url": self._response.url,
                    "method": method.upper(),
                }

                # Parse response
                try:
                    result["data"] = self._response.json()
                except ValueError:
                    result["data"] = self._response.text
                # Check for errors
                self._response.raise_for_status()
                self._last_result = result
                self._last_error = None
                self._last_request_time = datetime.now()

                return result

        except Exception as e:
            self._last_error = e
            raise
