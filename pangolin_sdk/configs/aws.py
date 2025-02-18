from dataclasses import dataclass, field
from typing import Optional, Dict
from pangolin_sdk.configs.base import ConnectionConfig
from pangolin_sdk.constants import AWSAuthMethod, AWSRegion, AWSService


@dataclass(kw_only=True)
class AWSConnectionConfig(ConnectionConfig):
    """Configuration for AWS connections"""

    auth_method: AWSAuthMethod = AWSAuthMethod.ACCESS_KEY
    region: AWSRegion = AWSRegion.US_EAST_1
    service: AWSService = AWSService.S3

    # For ACCESS_KEY authentication
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None

    # For PROFILE authentication
    profile_name: Optional[str] = None
    credentials_path: Optional[str] = None
    config_path: Optional[str] = None

    # For WEB_IDENTITY authentication
    role_arn: Optional[str] = None
    web_identity_token_file: Optional[str] = None

    # For SSO authentication
    sso_account_id: Optional[str] = None
    sso_role_name: Optional[str] = None
    sso_region: Optional[str] = None
    sso_start_url: Optional[str] = None

    # Common settings
    endpoint_url: Optional[str] = None
    api_version: Optional[str] = None
    verify_ssl: bool = True
    proxies: Dict[str, str] = field(default_factory=dict)
    assume_role_arn: Optional[str] = None

    def __post_init__(self):
        """Validate configuration after initialization"""
        super().__post_init__()

        if self.auth_method == AWSAuthMethod.ACCESS_KEY:
            if not (self.access_key_id and self.secret_access_key):
                raise ValueError(
                    "access_key_id and secret_access_key are required for ACCESS_KEY authentication"
                )

        elif self.auth_method == AWSAuthMethod.PROFILE:
            if not self.profile_name:
                raise ValueError("profile_name is required for PROFILE authentication")

        elif self.auth_method == AWSAuthMethod.WEB_IDENTITY:
            if not (self.role_arn and self.web_identity_token_file):
                raise ValueError(
                    "role_arn and web_identity_token_file are required for WEB_IDENTITY authentication"
                )

        elif self.auth_method == AWSAuthMethod.SSO:
            if not all(
                [
                    self.sso_account_id,
                    self.sso_role_name,
                    self.sso_region,
                    self.sso_start_url,
                ]
            ):
                raise ValueError(
                    "sso_account_id, sso_role_name, sso_region, and sso_start_url "
                    "are required for SSO authentication"
                )
