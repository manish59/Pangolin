from dataclasses import dataclass, field
from typing import Dict, Optional

from pangolin_sdk.configs.base import ConnectionConfig
from pangolin_sdk.constants import KubernetesAuthMethod


@dataclass(kw_only=True)
class KubernetesConnectionConfig(ConnectionConfig):
    """Configuration for Kubernetes connections"""

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

    def __post_init__(self):
        """Validate configuration after initialization"""
        super().__post_init__()

        if self.auth_method == KubernetesAuthMethod.CONFIG:
            if not self.kubeconfig_path and not self.in_cluster:
                raise ValueError(
                    "Either kubeconfig_path must be provided or in_cluster must be True "
                    "when using CONFIG authentication method"
                )

        elif self.auth_method == KubernetesAuthMethod.TOKEN:
            if not self.api_token:
                raise ValueError(
                    "API token is required for TOKEN authentication method"
                )

        elif self.auth_method == KubernetesAuthMethod.CERTIFICATE:
            if not all([self.client_cert_path, self.client_key_path]):
                raise ValueError(
                    "Both client certificate and key are required for CERTIFICATE authentication method"
                )

        elif self.auth_method == KubernetesAuthMethod.BASIC:
            if not all([self.username, self.password]):
                raise ValueError(
                    "Both username and password are required for BASIC authentication method"
                )

        # Normalize host (remove trailing slashes)
        if self.host:
            self.host = self.host.rstrip("/")
