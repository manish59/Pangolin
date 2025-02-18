"""AWS connection configuration module for the Pangolin SDK.

This module provides configuration classes for AWS connections, including
authentication methods and service-specific settings.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from pangolin_sdk.configs.base import ConnectionConfig
from pangolin_sdk.constants import AWSAuthMethod, AWSRegion, AWSService


@dataclass(kw_only=True)
class AWSConnectionConfig(ConnectionConfig):
    """Configuration for AWS connections.

    This class extends the base ConnectionConfig with AWS-specific settings
    including authentication methods, region configuration, and service selection.

    Attributes:
        auth_method: The AWS authentication method to use
        region: AWS region for the connection
        service: AWS service to connect to
        access_key_id: AWS access key ID for ACCESS_KEY auth
        secret_access_key: AWS secret access key for ACCESS_KEY auth
        session_token: Optional session token for temporary credentials
        profile_name: AWS profile name for PROFILE auth
        credentials_path: Path to AWS credentials file
        config_path: Path to AWS config file
        role_arn: ARN of the role to assume for WEB_IDENTITY auth
        web_identity_token_file: Path to web identity token file
        sso_account_id: AWS account ID for SSO auth
        sso_role_name: Role name for SSO auth
        sso_region: Region for SSO auth
        sso_start_url: SSO start URL
        endpoint_url: Custom endpoint URL if not using AWS default
        api_version: Specific API version to use
        verify_ssl: Whether to verify SSL certificates
        proxies: Proxy configuration for requests
        assume_role_arn: ARN of role to assume after initial authentication
    """

    auth_method: AWSAuthMethod = AWSAuthMethod.ACCESS_KEY
    region: AWSRegion = AWSRegion.US_EAST_1
    service: AWSService = AWSService.S3

    # ACCESS_KEY authentication settings
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None

    # PROFILE authentication settings
    profile_name: Optional[str] = None
    credentials_path: Optional[str] = None
    config_path: Optional[str] = None

    # WEB_IDENTITY authentication settings
    role_arn: Optional[str] = None
    web_identity_token_file: Optional[str] = None

    # SSO authentication settings
    sso_account_id: Optional[str] = None
    sso_role_name: Optional[str] = None
    sso_region: Optional[str] = None
    sso_start_url: Optional[str] = None

    # Common configuration settings
    endpoint_url: Optional[str] = None
    api_version: Optional[str] = None
    verify_ssl: bool = True
    proxies: Dict[str, str] = field(default_factory=dict)
    assume_role_arn: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate configuration after initialization.

        Raises:
            ValueError: If the authentication configuration is invalid
        """
        super().__post_init__()
        self._validate_auth_config()

    def _validate_auth_config(self) -> None:
        """Validate authentication configuration based on auth method.

        Raises:
            ValueError: If required authentication parameters are missing
        """
        validators = {
            AWSAuthMethod.ACCESS_KEY: self._validate_access_key_auth,
            AWSAuthMethod.PROFILE: self._validate_profile_auth,
            AWSAuthMethod.WEB_IDENTITY: self._validate_web_identity_auth,
            AWSAuthMethod.SSO: self._validate_sso_auth,
        }

        validator = validators.get(self.auth_method)
        if validator:
            validator()

    def _validate_access_key_auth(self) -> None:
        """Validate ACCESS_KEY authentication configuration.

        Raises:
            ValueError: If access key ID or secret access key is missing
        """
        if not (self.access_key_id and self.secret_access_key):
            raise ValueError(
                "access_key_id and secret_access_key are required for ACCESS_KEY authentication"
            )

    def _validate_profile_auth(self) -> None:
        """Validate PROFILE authentication configuration.

        Raises:
            ValueError: If profile name is missing
        """
        if not self.profile_name:
            raise ValueError("profile_name is required for PROFILE authentication")

    def _validate_web_identity_auth(self) -> None:
        """Validate WEB_IDENTITY authentication configuration.

        Raises:
            ValueError: If role ARN or web identity token file is missing
        """
        if not (self.role_arn and self.web_identity_token_file):
            raise ValueError(
                "role_arn and web_identity_token_file are required for WEB_IDENTITY authentication"
            )

    def _validate_sso_auth(self) -> None:
        """Validate SSO authentication configuration.

        Raises:
            ValueError: If any required SSO parameters are missing
        """
        required_sso_params = {
            "sso_account_id": self.sso_account_id,
            "sso_role_name": self.sso_role_name,
            "sso_region": self.sso_region,
            "sso_start_url": self.sso_start_url,
        }

        missing_params = [
            param for param, value in required_sso_params.items() if not value
        ]

        if missing_params:
            raise ValueError(
                f"The following parameters are required for SSO authentication: "
                f"{', '.join(missing_params)}"
            )
