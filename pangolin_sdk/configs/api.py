"""API configuration module for the Pangolin SDK.

This module provides configuration classes for API connections, including
header definitions and authentication methods.
"""

import base64
import hashlib
import hmac
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import jwt

from pangolin_sdk.configs.base import ConnectionConfig
from pangolin_sdk.constants import AuthMethod, HeaderRequirement
from pangolin_sdk.exceptions import AuthError


@dataclass
class HeaderDefinition:
    """Definition for an API header.

    Attributes:
        name: The name of the header
        requirement: The requirement level for this header
        default_value: Default value for the header if not specified
        allowed_values: List of allowed values for this header
        pattern: Regular expression pattern for header value validation
        description: Description of the header's purpose
    """

    name: str
    requirement: HeaderRequirement
    default_value: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    pattern: Optional[str] = None
    description: Optional[str] = None


@dataclass(kw_only=True)
class APIConfig(ConnectionConfig):
    """Extended configuration for API connections.

    This class extends the base ConnectionConfig with API-specific settings
    including authentication methods, tokens, and header configurations.

    Attributes:
        auth_method: The authentication method to use
        auth_token: Authentication token when using token-based auth
        api_key: API key for API key authentication
        api_key_name: Name of the API key header/parameter
        api_key_location: Location of the API key ("header" or "query")
        hmac_key: Key for HMAC authentication
        hmac_secret: Secret for HMAC authentication
        hmac_algorithm: Hash algorithm for HMAC (default: sha256)
        oauth_client_id: OAuth2 client ID
        oauth_client_secret: OAuth2 client secret
        oauth_scope: OAuth2 scope
        jwt_secret: Secret for JWT authentication
        jwt_algorithm: Algorithm for JWT (default: HS256)
        default_headers: Default headers to include in requests
        header_definitions: List of header definitions
    """

    auth_method: AuthMethod = AuthMethod.NONE
    auth_token: Optional[str] = None
    api_key: Optional[str] = None
    api_key_name: Optional[str] = None
    api_key_location: str = "header"

    # HMAC authentication settings
    hmac_key: Optional[str] = None
    hmac_secret: Optional[str] = None
    hmac_algorithm: str = "sha256"

    # OAuth2 settings
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    oauth_scope: Optional[str] = None

    # JWT settings
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"

    # Header settings
    default_headers: Dict[str, str] = field(
        default_factory=lambda: {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )
    header_definitions: List[HeaderDefinition] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        super().__post_init__()

        # Normalize host
        self.host = self.host.rstrip("/")

        # Validate auth configuration
        self._validate_auth_config()

        # Initialize default header definitions if none provided
        if not self.header_definitions:
            self._init_default_header_definitions()

    def _validate_auth_config(self) -> None:
        """Validate authentication configuration.

        Raises:
            AuthError: If the authentication configuration is invalid
        """
        auth_validators = {
            AuthMethod.BASIC: self._validate_basic_auth,
            AuthMethod.BEARER: self._validate_bearer_auth,
            AuthMethod.JWT: self._validate_jwt_auth,
            AuthMethod.API_KEY: self._validate_api_key_auth,
            AuthMethod.OAUTH2: self._validate_oauth2_auth,
            AuthMethod.HMAC: self._validate_hmac_auth,
        }

        validator = auth_validators.get(self.auth_method)
        if validator:
            validator()

    def _validate_basic_auth(self) -> None:
        """Validate basic authentication configuration."""
        if not (self.username and self.password):
            raise AuthError(
                message="Username and password required for basic authentication"
            )

    def _validate_bearer_auth(self) -> None:
        """Validate bearer token authentication configuration."""
        if not self.auth_token:
            raise AuthError(message="Token required for bearer authentication")

    def _validate_jwt_auth(self) -> None:
        """Validate JWT authentication configuration."""
        if not self.auth_token:
            raise AuthError(message="JWT token required for JWT authentication")
        try:
            jwt.decode(self.auth_token, options={"verify_signature": False})
        except jwt.InvalidTokenError as exc:
            raise AuthError(message="Invalid JWT token format") from exc

    def _validate_api_key_auth(self) -> None:
        """Validate API key authentication configuration."""
        if not (self.api_key and self.api_key_name):
            raise AuthError(
                message="API key and key name required for API key authentication"
            )

    def _validate_oauth2_auth(self) -> None:
        """Validate OAuth2 authentication configuration."""
        if not (self.oauth_client_id and self.oauth_client_secret):
            raise AuthError(message="Client ID and secret required for OAuth2")

    def _validate_hmac_auth(self) -> None:
        """Validate HMAC authentication configuration."""
        if not (self.hmac_key and self.hmac_secret):
            raise AuthError(message="Key and secret required for HMAC authentication")

    def get_auth_headers(
        self, request_data: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Get authentication headers based on the configured method.

        Args:
            request_data: Optional request data for methods like HMAC that need request info

        Returns:
            Dictionary of authentication headers

        Raises:
            AuthError: If authentication configuration is invalid
        """
        if self.auth_method == AuthMethod.NONE:
            return {}

        auth_header_getters = {
            AuthMethod.BASIC: self._get_basic_auth_headers,
            AuthMethod.BEARER: self._get_bearer_auth_headers,
            AuthMethod.JWT: self._get_jwt_auth_headers,
            AuthMethod.API_KEY: self._get_api_key_headers,
            AuthMethod.OAUTH2: self._get_oauth2_headers,
            AuthMethod.HMAC: lambda: self._get_hmac_headers(request_data),
        }

        getter = auth_header_getters.get(self.auth_method)
        return getter() if getter else {}

    def _get_basic_auth_headers(self) -> Dict[str, str]:
        """Get headers for basic authentication."""
        auth_string = base64.b64encode(
            f"{self.username}:{self.password}".encode()
        ).decode()
        return {"Authorization": f"Basic {auth_string}"}

    def _get_bearer_auth_headers(self) -> Dict[str, str]:
        """Get headers for bearer token authentication."""
        return {"Authorization": f"Bearer {self.auth_token}"}

    def _get_jwt_auth_headers(self) -> Dict[str, str]:
        """Get headers for JWT authentication."""
        return {"Authorization": f"Bearer {self.auth_token}"}

    def _get_api_key_headers(self) -> Dict[str, str]:
        """Get headers for API key authentication."""
        if self.api_key_location == "header":
            return {self.api_key_name: self.api_key}
        return {}

    def _get_oauth2_headers(self) -> Dict[str, str]:
        """Get headers for OAuth2 authentication."""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        raise AuthError(
            message="OAuth2 token not available. Authentication flow required."
        )

    def _get_hmac_headers(
        self, request_data: Optional[Dict[str, str]]
    ) -> Dict[str, str]:
        """Get headers for HMAC authentication."""
        if not request_data:
            raise AuthError(message="Request data required for HMAC authentication")

        timestamp = str(int(time.time()))
        string_to_sign = (
            f"{timestamp}:{self.hmac_key}:"
            f"{request_data.get('method', '')}:{request_data.get('path', '')}"
        )

        signature = hmac.new(
            self.hmac_secret.encode(),
            string_to_sign.encode(),
            getattr(hashlib, self.hmac_algorithm),
        ).hexdigest()

        return {
            "X-Timestamp": timestamp,
            "X-API-Key": self.hmac_key,
            "X-Signature": signature,
        }

    def _init_default_header_definitions(self) -> None:
        """Initialize default header definitions."""
        self.header_definitions = [
            HeaderDefinition(
                name="Content-Type",
                requirement=HeaderRequirement.REQUIRED,
                default_value="application/json",
                allowed_values=["application/json", "application/xml", "text/plain"],
                description="The content type of the request body",
            ),
            HeaderDefinition(
                name="Accept",
                requirement=HeaderRequirement.REQUIRED,
                default_value="application/json",
                allowed_values=["application/json", "application/xml", "text/plain"],
                description="The expected response content type",
            ),
            HeaderDefinition(
                name="User-Agent",
                requirement=HeaderRequirement.OPTIONAL,
                default_value="Python-APIClient/1.0",
                description="Client identification",
            ),
        ]

    def get_full_url(self, endpoint: str = "") -> str:
        """Get full URL for an endpoint.

        Args:
            endpoint: The API endpoint path

        Returns:
            Complete URL including host and endpoint
        """
        if not endpoint:
            return self.host
        return f"{self.host}/{endpoint.lstrip('/')}"
