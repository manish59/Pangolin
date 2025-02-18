from dataclasses import dataclass, field
from typing import Optional, Dict, List
import base64
import hmac
import hashlib
import time
import jwt
from pangolin_sdk.configs.base import ConnectionConfig
from pangolin_sdk.exceptions import AuthError
from pangolin_sdk.constants import AuthMethod, HeaderRequirement


@dataclass
class HeaderDefinition:
    """Definition for an API header"""

    name: str
    requirement: HeaderRequirement
    default_value: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    pattern: Optional[str] = None
    description: Optional[str] = None


@dataclass(kw_only=True)
class APIConfig(ConnectionConfig):
    """Extended configuration for API connections"""

    # Authentication
    auth_method: AuthMethod = AuthMethod.NONE
    auth_token: Optional[str] = None
    api_key: Optional[str] = None
    api_key_name: Optional[str] = None
    api_key_location: str = "header"  # "header" or "query"

    # For HMAC auth
    hmac_key: Optional[str] = None
    hmac_secret: Optional[str] = None
    hmac_algorithm: str = "sha256"

    # For OAuth2
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    oauth_scope: Optional[str] = None

    # For JWT specific
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"

    # Headers
    default_headers: Dict[str, str] = field(
        default_factory=lambda: {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )
    header_definitions: List[HeaderDefinition] = field(default_factory=list)

    def __post_init__(self):
        """Validate configuration after initialization"""
        super().__post_init__() if hasattr(super(), "__post_init__") else None

        # Normalize host
        self.host = self.host.rstrip("/")

        # Validate auth configuration
        self._validate_auth_config()

        # Initialize default header definitions if none provided
        if not self.header_definitions:
            self._init_default_header_definitions()

    def _validate_auth_config(self):
        """Validate authentication configuration"""
        if self.auth_method == AuthMethod.BASIC:
            if not (self.username and self.password):
                raise AuthError(
                    "Username and password required for basic authentication"
                )

        elif self.auth_method == AuthMethod.BEARER:
            if not self.auth_token:
                raise AuthError("Token required for bearer authentication")

        elif self.auth_method == AuthMethod.JWT:
            if not self.auth_token:
                raise AuthError("JWT token required for JWT authentication")
            try:
                # Verify JWT format without validating signature
                jwt.decode(self.auth_token, options={"verify_signature": False})
            except jwt.InvalidTokenError:
                raise AuthError("Invalid JWT token format")

        elif self.auth_method == AuthMethod.API_KEY:
            if not (self.api_key and self.api_key_name):
                raise AuthError(
                    "API key and key name required for API key authentication"
                )

        elif self.auth_method == AuthMethod.OAUTH2:
            if not (self.oauth_client_id and self.oauth_client_secret):
                raise AuthError("Client ID and secret required for OAuth2")

        elif self.auth_method == AuthMethod.HMAC:
            if not (self.hmac_key and self.hmac_secret):
                raise AuthError("Key and secret required for HMAC authentication")

    def get_auth_headers(self, request_data: Optional[Dict] = None) -> Dict[str, str]:
        """
        Get authentication headers based on the configured method
        Args:
            request_data: Optional request data for methods like HMAC that need request info
        Returns:
            Dict of headers
        """
        headers = {}

        if self.auth_method == AuthMethod.NONE:
            return headers

        elif self.auth_method == AuthMethod.BASIC:
            auth_string = base64.b64encode(
                f"{self.username}:{self.password}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {auth_string}"

        elif self.auth_method == AuthMethod.BEARER:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        elif self.auth_method == AuthMethod.JWT:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        elif self.auth_method == AuthMethod.API_KEY:
            if self.api_key_location == "header":
                headers[self.api_key_name] = self.api_key

        elif self.auth_method == AuthMethod.OAUTH2:
            if self.auth_token:  # If we have a token from previous auth
                headers["Authorization"] = f"Bearer {self.auth_token}"
            else:
                # In real implementation, you'd handle the OAuth2 flow here
                raise AuthError(
                    "OAuth2 token not available. Authentication flow required."
                )

        elif self.auth_method == AuthMethod.HMAC:
            if request_data:
                timestamp = str(int(time.time()))
                # Create string to sign
                string_to_sign = f"{timestamp}:{self.hmac_key}:{request_data.get('method', '')}:{request_data.get('path', '')}"

                # Create signature
                signature = hmac.new(
                    self.hmac_secret.encode(),
                    string_to_sign.encode(),
                    getattr(hashlib, self.hmac_algorithm),
                ).hexdigest()

                headers.update(
                    {
                        "X-Timestamp": timestamp,
                        "X-API-Key": self.hmac_key,
                        "X-Signature": signature,
                    }
                )
            else:
                raise AuthError("Request data required for HMAC authentication")

        elif self.auth_method == AuthMethod.DIGEST:
            pass

        return headers

    def _init_default_header_definitions(self):
        """Initialize default header definitions"""
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
        """Get full URL for an endpoint"""
        if not endpoint:
            return self.host
        return f"{self.host}/{endpoint.lstrip('/')}"
