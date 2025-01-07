import logging
import requests

from typing import Any, Dict, Optional, Union
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from urllib.parse import urljoin

from pangolin_sdk.config import PangolinConfig
from pangolin_sdk.exceptions import APIConnectionError, APIExecutionError
from pangolin_sdk.engine import Engine


class API_Engine(Engine):
    """
    A flexible API interaction engine supporting multiple HTTP methods.

    Supports:
    - GET, POST, PUT, PATCH, DELETE requests
    - Authentication methods
    - Custom headers
    - Proxy support
    - Retry mechanisms
    """

    def __init__(
        self,
        base_url: str,
        auth_type: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **config,
    ):
        """
        Initialize the API Engine.

        Args:
            base_url (str): Base URL for API interactions
            auth_type (Optional[str]): Authentication type ('basic', 'digest', or None)
            username (Optional[str]): Username for authentication
            password (Optional[str]): Password for authentication
            **config: Additional configuration options
        """
        # Default configuration
        super().__init__(**config)
        self.config = {
            "timeout": PangolinConfig.DEFAULT_TIMEOUT,
            "logging_enabled": PangolinConfig.LOGGING_ENABLED,
            "connection_retries": PangolinConfig.CONNECTION_RETRIES,
            "verify_ssl": True,
            "proxies": None,
        }
        self.config.update(config)

        # Logging setup

        # API connection parameters
        self.base_url = base_url
        self._auth = self._setup_authentication(auth_type, username, password)

        # Request state
        self._session = requests.Session()

    def _setup_authentication(self, auth_type, username, password):
        """
        Setup authentication based on provided credentials.

        Returns:
            Union[Callable, Dict, None]: Authentication method
        """
        try:
            if auth_type == "basic":
                return HTTPBasicAuth(username, password)

            elif auth_type == "digest":
                return HTTPDigestAuth(username, password)

            elif auth_type == "token":
                return {"Authorization": f"Bearer {self.config.get('token')}"}

            elif auth_type == "api_key":
                # Support different API key placements
                key = self.config.get("api_key")
                key_location = self.config.get("key_location", "header")

                if key_location == "header":
                    return {"X-API-Key": key}
                elif key_location == "query":
                    return {"params": {"api_key": key}}

            elif auth_type == "custom_header":
                return {
                    self.config.get("header_name", "X-Custom-Auth"): self.config.get(
                        "header_value"
                    )
                }

            return None

        except Exception as e:
            self.logger.error(f"Authentication setup failed: {e}")
            raise

    def setup(self) -> None:
        """
        Prepare the API engine for interactions.
        Performs initial connection validation.

        Raises:
            APIConnectionError: If initial connection fails
        """
        try:
            # Validate base URL connectivity
            response = self._session.get(
                self.base_url,
                auth=self._auth,
                timeout=self.config["timeout"],
                verify=self.config["verify_ssl"],
                proxies=self.config["proxies"],
            )
            response.raise_for_status()

            self.logger.info(f"Successfully connected to {self.base_url}")

        except requests.RequestException as e:
            error_msg = f"Failed to connect to {self.base_url}: {str(e)}"
            self.logger.error(error_msg)
            self._last_error = error_msg
            raise APIConnectionError(error_msg)

    def execute(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute an API request.

        Args:
            endpoint (str): API endpoint
            method (str, optional): HTTP method. Defaults to 'GET'
            data (Optional[Dict[str, Any]], optional): Request payload
            params (Optional[Dict[str, Any]], optional): Query parameters
            headers (Optional[Dict[str, str]], optional): Custom headers
            **kwargs: Additional arguments for requests library

        Returns:
            Dict[str, Any]: Response data

        Raises:
            APIExecutionError: If request execution fails
        """
        # Prepare full URL
        full_url = urljoin(self.base_url, endpoint)

        # Prepare request arguments
        request_args = {
            "url": full_url,
            "method": method.upper(),
            "auth": self._auth,
            "timeout": self.config["timeout"],
            "verify": self.config["verify_ssl"],
            "proxies": self.config["proxies"],
        }

        # Add optional parameters
        if data is not None:
            request_args["json"] = data
        if params is not None:
            request_args["params"] = params
        if headers is not None:
            request_args["headers"] = headers

        # Add any additional kwargs
        request_args.update(kwargs)

        try:
            # Log request details
            self.logger.info(f"Executing {method.upper()} request to {full_url}")

            # Execute request
            response = self._session.request(**request_args)

            # Raise exception for HTTP errors
            response.raise_for_status()

            # Store last response
            self._last_query_result = response

            # Parse and return response
            try:
                response_data = response.json()
            except ValueError:
                response_data = response.text

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": response_data,
            }

        except requests.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            self.logger.error(error_msg)
            self._last_error = error_msg
            raise APIExecutionError(error_msg)

    def result(self) -> Optional[Dict[str, Any]]:
        """
        Get the result of the last API request.

        Returns:
            Optional[Dict[str, Any]]: Last API response data
        """
        if self._last_query_result:
            return (
                self._last_query_result.json() if self._last_query_result.text else None
            )
        return None

    def error(self) -> Optional[str]:
        """
        Get the error message from the last operation.

        Returns:
            Optional[str]: Last error message
        """
        return self._last_error


# Example usage
def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Create API engine with basic authentication
        api_engine = API_Engine(
            base_url="https://jsonplaceholder.typicode.com",
            auth_type="basic",
            username="user",
            password="pass",
            verify_ssl=True,
        )

        # Setup connection
        api_engine.setup()

        # GET request example
        get_response = api_engine.execute("/posts/1")
        print("GET Response:", get_response)

        # POST request example
        post_data = {"title": "foo", "body": "bar", "userId": 1}
        post_response = api_engine.execute("/posts", method="POST", data=post_data)
        print("POST Response:", post_response)

        # PUT request example
        put_data = {
            "id": 1,
            "title": "updated title",
            "body": "updated body",
            "userId": 1,
        }
        put_response = api_engine.execute("/posts/1", method="PUT", data=put_data)
        print("PUT Response:", put_response)

        # PATCH request example
        patch_data = {"title": "patched title"}
        patch_response = api_engine.execute("/posts/1", method="PATCH", data=patch_data)
        print("PATCH Response:", patch_response)

        # DELETE request example
        delete_response = api_engine.execute("/posts/1", method="DELETE")
        print("DELETE Response:", delete_response)

    except Exception as e:
        print(f"API interaction error: {e}")


if __name__ == "__main__":
    main()
