from typing import Any, Dict, Optional, Union
from kubernetes import client, config
from kubernetes.client import ApiClient
from kubernetes.config import ConfigException

from pangolin_sdk.connections.base import BaseConnection
from pangolin_sdk.configs.kubernetes import KubernetesConnectionConfig
from pangolin_sdk.constants import (
    KubernetesAuthMethod,
    ConnectionStatus,
    KubernetesResourceType,
)
from pangolin_sdk.exceptions import ConnectionError, ExecutionError


class KubernetesConnection(BaseConnection[ApiClient]):
    """Implementation of Kubernetes connection handling."""

    def __init__(self, config: KubernetesConnectionConfig):
        """Initialize Kubernetes connection."""
        super().__init__(config)
        self.config = config
        self._api_client = None
        self._core_api = None
        self._apps_api = None
        self._networking_api = None
        self._custom_objects_api = None

    def _connect_impl(self) -> ApiClient:
        """
        Implements connection logic for Kubernetes.

        Returns:
            kubernetes.client.ApiClient: Kubernetes API client

        Raises:
            ConnectionError: If connection fails
        """
        try:
            if self.config.auth_method == KubernetesAuthMethod.CONFIG:
                if self.config.in_cluster:
                    config.load_incluster_config()
                else:
                    config.load_kube_config(
                        config_file=self.config.kubeconfig_path,
                        context=self.config.context,
                    )
                self._api_client = ApiClient()

            elif self.config.auth_method == KubernetesAuthMethod.TOKEN:
                configuration = client.Configuration()
                configuration.host = f"https://{self.config.host}:{self.config.port}"
                configuration.api_key = {
                    "authorization": f"Bearer {self.config.api_token}"
                }
                configuration.verify_ssl = self.config.verify_ssl
                if self.config.ca_cert_path:
                    configuration.ssl_ca_cert = self.config.ca_cert_path
                self._api_client = ApiClient(configuration)

            elif self.config.auth_method == KubernetesAuthMethod.CERTIFICATE:
                configuration = client.Configuration()
                configuration.host = f"https://{self.config.host}:{self.config.port}"
                configuration.cert_file = self.config.client_cert_path
                configuration.key_file = self.config.client_key_path
                configuration.verify_ssl = self.config.verify_ssl
                if self.config.ca_cert_path:
                    configuration.ssl_ca_cert = self.config.ca_cert_path
                self._api_client = ApiClient(configuration)

            elif self.config.auth_method == KubernetesAuthMethod.BASIC:
                configuration = client.Configuration()
                configuration.host = f"https://{self.config.host}:{self.config.port}"
                configuration.username = self.config.username
                configuration.password = self.config.password
                configuration.verify_ssl = self.config.verify_ssl
                if self.config.ca_cert_path:
                    configuration.ssl_ca_cert = self.config.ca_cert_path
                self._api_client = ApiClient(configuration)

            # Initialize API interfaces
            self._core_api = client.CoreV1Api(self._api_client)
            self._apps_api = client.AppsV1Api(self._api_client)
            self._networking_api = client.NetworkingV1Api(self._api_client)
            self._custom_objects_api = client.CustomObjectsApi(self._api_client)

            return self._api_client

        except (ConfigException, Exception) as e:
            error = ConnectionError(
                message=f"Failed to connect to Kubernetes cluster: {str(e)}",
                details=self.config.get_info(),
            )
            raise error

    def _execute_impl(
        self, resource_type: KubernetesResourceType, action: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Execute Kubernetes operations.

        Args:
            resource_type: Type of Kubernetes resource to operate on
            action: Action to perform (list, get, create, delete, update, etc.)
            **kwargs: Additional arguments for the operation

        Returns:
            Dict containing operation results

        Raises:
            ExecutionError: If execution fails
        """
        try:
            namespace = kwargs.get("namespace", self.config.namespace)
            name = kwargs.get("name")
            body = kwargs.get("body")

            # Get appropriate API based on resource type
            api = self._get_api_for_resource(resource_type)

            # Build method name (e.g., list_namespaced_pod)
            method_name = self._build_method_name(resource_type, action, namespace)

            # Get the method
            method = getattr(api, method_name)

            # Build arguments
            method_args = self._build_method_args(action, namespace, name, body)

            # Execute the method
            result = method(**method_args)

            # Convert response to dict
            return self._api_client.sanitize_for_serialization(result)

        except Exception as e:
            error = ExecutionError(
                message=f"Failed to execute Kubernetes operation: {str(e)}",
                details={
                    "resource_type": resource_type.value,
                    "action": action,
                    "arguments": kwargs,
                },
            )
            raise error

    def _disconnect_impl(self) -> None:
        """
        Implements disconnection logic for Kubernetes.

        Raises:
            ConnectionError: If disconnection fails
        """
        try:
            if self._api_client:
                self._api_client.close()
                self._api_client = None
                self._core_api = None
                self._apps_api = None
                self._networking_api = None
                self._custom_objects_api = None
        except Exception as e:
            error = ConnectionError(
                message=f"Failed to disconnect from Kubernetes cluster: {str(e)}",
                details=self.config.get_info(),
            )
            raise error

    def _get_api_for_resource(self, resource_type: KubernetesResourceType) -> Any:
        """Get appropriate API interface for the resource type."""
        api_mapping = {
            KubernetesResourceType.POD: self._core_api,
            KubernetesResourceType.SERVICE: self._core_api,
            KubernetesResourceType.CONFIGMAP: self._core_api,
            KubernetesResourceType.SECRET: self._core_api,
            KubernetesResourceType.NAMESPACE: self._core_api,
            KubernetesResourceType.NODE: self._core_api,
            KubernetesResourceType.DEPLOYMENT: self._apps_api,
            KubernetesResourceType.STATEFULSET: self._apps_api,
            KubernetesResourceType.DAEMONSET: self._apps_api,
            KubernetesResourceType.INGRESS: self._networking_api,
        }
        return api_mapping.get(resource_type, self._core_api)

    def _build_method_name(
        self,
        resource_type: KubernetesResourceType,
        action: str,
        namespace: Optional[str] = None,
    ) -> str:
        """Build method name based on resource type and action."""
        resource = resource_type.value.lower()

        # Handle cluster-scoped resources
        if resource_type in [
            KubernetesResourceType.NODE,
            KubernetesResourceType.NAMESPACE,
        ]:
            return f"{action}_{resource}"

        # Handle namespaced resources
        return f"{action}_namespaced_{resource}"

    def _build_method_args(
        self,
        action: str,
        namespace: Optional[str],
        name: Optional[str],
        body: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Build method arguments based on action type."""
        args = {}

        if namespace:
            args["namespace"] = namespace

        if name and action in ["get", "delete", "patch", "replace"]:
            args["name"] = name

        if body and action in ["create", "patch", "replace"]:
            args["body"] = body

        return args
