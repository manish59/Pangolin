"""Kubernetes connection configuration module for Pangolin SDK.

This module provides configuration classes for Kubernetes connections,
supporting various authentication methods and cluster configurations.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from pangolin_sdk.configs.base import ConnectionConfig
from pangolin_sdk.constants import KubernetesAuthMethod


@dataclass(kw_only=True)
class KubernetesConnectionConfig(ConnectionConfig):
    """Configuration for Kubernetes connections.

    This class extends the base ConnectionConfig with Kubernetes-specific
    parameters and validation logic.

    Attributes:
        auth_method: Authentication method for Kubernetes
        context: Kubernetes context name
        kubeconfig_path: Path to kubeconfig file
        api_token: API token for token-based authentication
        ca_cert_path: Path to CA certificate
        client_cert_path: Path to client certificate
        client_key_path: Path to client key
        namespace: Kubernetes namespace
        verify_ssl: Whether to verify SSL certificates
        api_version: Kubernetes API version
        port: Kubernetes API server port
        headers: Additional HTTP headers for API requests
        in_cluster: Whether running inside a Kubernetes cluster
    """

    auth_method: KubernetesAuthMethod = KubernetesAuthMethod.CONFIG
    context: Optional[str] = None
    kubeconfig_path: Optional[str] = None
    api_token: Optional[str] = None
    ca_cert_path: Optional[str] = None
    client_cert_path: Optional[str] = None
    client_key_path: Optional[str] = None
    namespace: str = "default"
    verify_ssl: bool = True
    api_version: str = "v1"
    port: int = 6443
    headers: Dict[str, str] = field(default_factory=dict)
    in_cluster: bool = False

    def __post_init__(self) -> None:
        """Validate configuration after initialization.

        Raises:
            ValueError: If the authentication configuration is invalid
        """
        super().__post_init__()
        self._validate_auth_config()
        self._normalize_host()

    def _validate_auth_config(self) -> None:
        """Validate authentication configuration based on auth method.

        Raises:
            ValueError: If required authentication parameters are missing
        """
        validators = {
            KubernetesAuthMethod.CONFIG: self._validate_config_auth,
            KubernetesAuthMethod.TOKEN: self._validate_token_auth,
            KubernetesAuthMethod.CERTIFICATE: self._validate_certificate_auth,
            KubernetesAuthMethod.BASIC: self._validate_basic_auth,
        }

        validator = validators.get(self.auth_method)
        if validator:
            validator()

    def _validate_config_auth(self) -> None:
        """Validate CONFIG authentication method.

        Raises:
            ValueError: If neither kubeconfig path nor in-cluster flag is set
        """
        if not self.kubeconfig_path and not self.in_cluster:
            raise ValueError(
                "Either kubeconfig_path must be provided or in_cluster must be True "
                "when using CONFIG authentication method"
            )

    def _validate_token_auth(self) -> None:
        """Validate TOKEN authentication method.

        Raises:
            ValueError: If API token is missing
        """
        if not self.api_token:
            raise ValueError("API token is required for TOKEN authentication method")

    def _validate_certificate_auth(self) -> None:
        """Validate CERTIFICATE authentication method.

        Raises:
            ValueError: If client certificate or key is missing
        """
        if not all([self.client_cert_path, self.client_key_path]):
            raise ValueError(
                "Both client certificate and key are required for CERTIFICATE "
                "authentication method"
            )

    def _validate_basic_auth(self) -> None:
        """Validate BASIC authentication method.

        Raises:
            ValueError: If username or password is missing
        """
        if not all([self.username, self.password]):
            raise ValueError(
                "Both username and password are required for BASIC authentication method"
            )

    def _normalize_host(self) -> None:
        """Normalize host URL by removing trailing slashes."""
        if self.host:
            self.host = self.host.rstrip("/")
