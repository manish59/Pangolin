"""Kubernetes Connection Handling Module.

This module provides implementation for Kubernetes connection and resource management.
"""

import logging
from typing import Any, Dict, Optional, Union

from kubernetes import client, config
from kubernetes.client import ApiClient
from kubernetes.config import ConfigException

from pangolin_sdk.configs.kubernetes import KubernetesConnectionConfig
from pangolin_sdk.connections.base import BaseConnection
from pangolin_sdk.constants import KubernetesAuthMethod, KubernetesResourceType
from pangolin_sdk.exceptions import (
    BaseConnectionError as ConnectionError,
    BaseExecutionError as ExecutionError,
)


class KubernetesConnection(BaseConnection[ApiClient]):
    """Implementation of Kubernetes connection handling.

    Attributes:
        config (KubernetesConnectionConfig): Kubernetes connection configuration.
        _api_client (Optional[ApiClient]): Kubernetes API client.
        _core_api (Optional[client.CoreV1Api]): Core Kubernetes API.
        _apps_api (Optional[client.AppsV1Api]): Apps Kubernetes API.
        _networking_api (Optional[client.NetworkingV1Api]): Networking Kubernetes API.
        _custom_objects_api (Optional[client.CustomObjectsApi]): Custom objects API.
    """

    def __init__(self, config: KubernetesConnectionConfig):
        """
        Initialize Kubernetes connection.

        Args:
            config (KubernetesConnectionConfig): Kubernetes connection configuration.
        """
        super().__init__(config)
        self.config = config
        self._api_client: Optional[ApiClient] = None
        self._core_api: Optional[client.CoreV1Api] = None
        self._apps_api: Optional[client.AppsV1Api] = None
        self._networking_api: Optional[client.NetworkingV1Api] = None
        self._custom_objects_api: Optional[client.CustomObjectsApi] = None
        self._logger = logging.getLogger(__name__)

    def _connect_impl(self) -> ApiClient:
        """
        Implements connection logic for Kubernetes.

        Returns:
            kubernetes.client.ApiClient: Kubernetes API client

        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Authentication method handling
            auth_method_handlers = {
                KubernetesAuthMethod.CONFIG: self._configure_config_auth,
                KubernetesAuthMethod.TOKEN: self._configure_token_auth,
                KubernetesAuthMethod.CERTIFICATE: self._configure_certificate_auth,
                KubernetesAuthMethod.BASIC: self._configure_basic_auth,
            }

            handler = auth_method_handlers.get(self.config.auth_method)
            if not handler:
                raise ValueError(f"Unsupported authentication method: {self.config.auth_method}")

            self._api_client = handler()

            # Initialize API interfaces
            self._initialize_api_interfaces()

            return self._api_client

        except (ConfigException, Exception) as e:
            error = ConnectionError(
                message=f"Failed to connect to Kubernetes cluster: {e}",
                details=self.config.get_info(),
            )
            self._logger.error("Kubernetes connection error: %s", str(error))
            raise error from e

    def _configure_config_auth(self) -> ApiClient:
        """
        Configure authentication using Kubernetes config.

        Returns:
            ApiClient: Configured API client
        """
        if self.config.in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config(
                config_file=self.config.kubeconfig_path,
                context=self.config.context,
            )
        return ApiClient()

    def _configure_token_auth(self) -> ApiClient:
        """
        Configure authentication using API token.

        Returns:
            ApiClient: Configured API client
        """
        configuration = client.Configuration()
        configuration.host = f"https://{self.config.host}:{self.config.port}"
        configuration.api_key = {
            "authorization": f"Bearer {self.config.api_token}"
        }
        configuration.verify_ssl = self.config.verify_ssl
        if self.config.ca_cert_path:
            configuration.ssl_ca_cert = self.config.ca_cert_path
        return ApiClient(configuration)

    def _configure_certificate_auth(self) -> ApiClient:
        """
        Configure authentication using client certificate.

        Returns:
            ApiClient: Configured API client
        """
        configuration = client.Configuration()
        configuration.host = f"https://{self.config.host}:{self.config.port}"
        configuration.cert_file = self.config.client_cert_path
        configuration.key_file = self.config.client_key_path
        configuration.verify_ssl = self.config.verify_ssl
        if self.config.ca_cert_path:
            configuration.ssl_ca_cert = self.config.ca_cert_path
        return ApiClient(configuration)

    def _configure_basic_auth(self) -> ApiClient:
        """
        Configure authentication using basic credentials.

        Returns:
            ApiClient: Configured API client
        """
        configuration = client.Configuration()
        configuration.host = f"https://{self.config.host}:{self.config.port}"
        configuration.username = self.config.username
        configuration.password = self.config.password
        configuration.verify_ssl = self.config.verify_ssl
        if self.config.ca_cert_path:
            configuration.ssl_ca_cert = self.config.ca_cert_path
        return ApiClient(configuration)

    def _initialize_api_interfaces(self) -> None:
        """Initialize Kubernetes API interfaces."""
        if not self._api_client:
            raise ValueError("API client not initialized")

        self._core_api = client.CoreV1Api(self._api_client)
        self._apps_api = client.AppsV1Api(self._api_client)
        self._networking_api = client.NetworkingV1Api(self._api_client)
        self._custom_objects_api = client.CustomObjectsApi(self._api_client)

    def _execute_impl(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute Kubernetes operations.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments for Kubernetes operation

        Returns:
            Dict containing operation results

        Raises:
            ExecutionError: If execution fails
        """
        # If specific Kubernetes arguments are provided
        if 'resource_type' in kwargs and 'action' in kwargs:
            return self._execute_kubernetes_operation(
                resource_type=kwargs['resource_type'],
                action=kwargs['action'],
                **{k: v for k, v in kwargs.items() if k not in ['resource_type', 'action']}
            )

        # Fallback to base implementation or raise an error
        raise ExecutionError(
            message="Invalid arguments for Kubernetes execution",
            details=kwargs
        )

    def _execute_kubernetes_operation(
        self,
        resource_type: KubernetesResourceType,
        action: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a specific Kubernetes operation.

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
                message=f"Failed to execute Kubernetes operation: {e}",
                details={
                    "resource_type": resource_type.value,
                    "action": action,
                    "arguments": kwargs,
                },
            )
            self._logger.error("Kubernetes execution error: %s", str(error))
            raise error from e

    def _disconnect_impl(self) -> None:
        """
        Implements disconnection logic for Kubernetes.

        Raises:
            ConnectionError: If disconnection fails
        """
        try:
            if self._api_client:
                self._api_client.close()
                self._reset_api_interfaces()
        except Exception as e:
            error = ConnectionError(
                message=f"Failed to disconnect from Kubernetes cluster: {e}",
                details=self.config.get_info(),
            )
            self._logger.error("Kubernetes disconnection error: %s", str(error))
            raise error from e

    def _reset_api_interfaces(self) -> None:
        """Reset all API interfaces to None."""
        self._api_client = None
        self._core_api = None
        self._apps_api = None
        self._networking_api = None
        self._custom_objects_api = None

    def _get_api_for_resource(self, resource_type: KubernetesResourceType) -> Any:
        """
        Get appropriate API interface for the resource type.

        Args:
            resource_type: Kubernetes resource type

        Returns:
            Appropriate API interface for the resource
        """
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
        """
        Build method name based on resource type and action.

        Args:
            resource_type: Kubernetes resource type
            action: Operation to perform
            namespace: Namespace (optional)

        Returns:
            Constructed method name
        """
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
        """
        Build method arguments based on action type.

        Args:
            action: Operation to perform
            namespace: Kubernetes namespace
            name: Resource name
            body: Request body (optional)

        Returns:
            Dictionary of method arguments
        """
        args: Dict[str, Any] = {}

        if namespace:
            args["namespace"] = namespace

        if name and action in ["get", "delete", "patch", "replace"]:
            args["name"] = name

        if body and action in ["create", "patch", "replace"]:
            args["body"] = body

        return args
