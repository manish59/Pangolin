"""AWS Connection Handling Module.

This module provides implementation for AWS service connections 
and operations using the boto3 library.
"""

import logging
from typing import Any, Dict, Optional

import boto3
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError

from pangolin_sdk.configs.aws import AWSConnectionConfig
from pangolin_sdk.connections.base import BaseConnection
from pangolin_sdk.constants import AWSAuthMethod, AWSService
from pangolin_sdk.exceptions import BaseConnectionError as ConnectionError, BaseExecutionError as ExecutionError


class AWSConnection(BaseConnection[BaseClient]):
    """Implementation of AWS connection handling.

    Attributes:
        config (AWSConnectionConfig): AWS connection configuration.
        _session (Optional[boto3.Session]): AWS boto3 session.
        _client (Optional[BaseClient]): AWS service client.
        _resource (Optional[Any]): AWS service resource.
    """

    def __init__(self, config: AWSConnectionConfig):
        """
        Initialize AWS connection.

        Args:
            config (AWSConnectionConfig): AWS connection configuration.
        """
        super().__init__(config)
        self.config = config
        self._session: Optional[boto3.Session] = None
        self._client: Optional[BaseClient] = None
        self._resource: Optional[Any] = None
        self._logger = logging.getLogger(__name__)

    def _connect_impl(self) -> BaseClient:
        """
        Implements connection logic for AWS.

        Returns:
            botocore.client.BaseClient: AWS service client

        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Prepare session creation arguments
            kwargs = self._prepare_session_kwargs()

            # Create session based on authentication method
            session = self._create_aws_session()

            # Store session
            self._session = session

            # Create service client and resource
            self._create_service_interfaces(session, kwargs)

            # Test connection
            self._test_connection()

            return self._client

        except (BotoCoreError, ClientError) as e:
            error = ConnectionError(
                message=f"Failed to connect to AWS: {e}",
                details=self.config.get_info(),
            )
            self._logger.error("AWS connection error: %s", str(error))
            raise error from e

    def _prepare_session_kwargs(self) -> Dict[str, Any]:
        """
        Prepare keyword arguments for AWS session and client creation.

        Returns:
            Dict of session and client configuration parameters.
        """
        kwargs = {"region_name": self.config.region.value}

        if self.config.endpoint_url:
            kwargs["endpoint_url"] = self.config.endpoint_url

        if self.config.verify_ssl is not None:
            kwargs["verify"] = self.config.verify_ssl

        if self.config.api_version:
            kwargs["api_version"] = self.config.api_version

        return kwargs

    def _create_aws_session(self) -> boto3.Session:
        """
        Create AWS session based on authentication method.

        Returns:
            boto3.Session: Configured AWS session.

        Raises:
            ValueError: If authentication method is unsupported.
        """
        auth_method_map = {
            AWSAuthMethod.ACCESS_KEY: self._create_access_key_session,
            AWSAuthMethod.PROFILE: self._create_profile_session,
            AWSAuthMethod.INSTANCE_ROLE: self._create_instance_role_session,
            AWSAuthMethod.WEB_IDENTITY: self._create_web_identity_session,
            AWSAuthMethod.SSO: self._create_sso_session,
        }

        handler = auth_method_map.get(self.config.auth_method)
        if not handler:
            raise ValueError(
                f"Unsupported authentication method: {self.config.auth_method}"
            )

        return handler()

    def _create_access_key_session(self) -> boto3.Session:
        """Create session using access key credentials."""
        return boto3.Session(
            aws_access_key_id=self.config.access_key_id,
            aws_secret_access_key=self.config.secret_access_key,
            aws_session_token=self.config.session_token,
        )

    def _create_profile_session(self) -> boto3.Session:
        """Create session using AWS profile."""
        return boto3.Session(profile_name=self.config.profile_name)

    def _create_instance_role_session(self) -> boto3.Session:
        """Create session using instance role."""
        return boto3.Session()

    def _create_web_identity_session(self) -> boto3.Session:
        """Create session for web identity (uses environment variables)."""
        return boto3.Session()

    def _create_sso_session(self) -> boto3.Session:
        """Create session using SSO."""
        return boto3.Session(profile_name=self.config.profile_name)

    def _create_service_interfaces(
            self, session: boto3.Session, kwargs: Dict[str, Any]
    ) -> None:
        """
        Create service client and resource interfaces.

        Args:
            session (boto3.Session): AWS session.
            kwargs (Dict[str, Any]): Configuration parameters.
        """
        # Create service client
        self._client = session.client(self.config.service.value, **kwargs)

        # Optionally create service resource
        try:
            self._resource = session.resource(self.config.service.value, **kwargs)
        except Exception:
            # Not all services have resource interface
            self._resource = None

    def _execute_impl(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute AWS operations with flexible arguments.

        Args:
            *args: Positional arguments (unused)
            **kwargs: Keyword arguments for AWS operation
                Expected keys:
                - operation (str): The AWS API operation to perform
                - using (str, optional): Interface to use ('client' or 'resource')
                - Additional arguments for the specific operation

        Returns:
            Dict containing operation results

        Raises:
            ExecutionError: If execution fails
        """
        # Extract specific AWS operation parameters
        operation = kwargs.get('operation')
        using = kwargs.get('using', 'client')

        # Validate operation is provided
        if not operation:
            raise ValueError("Operation must be specified")

        try:
            # Choose interface
            interface = self._client if using == "client" else self._resource
            if not interface:
                raise ValueError(f"AWS {using} interface not available")

            # Get the operation method
            method = getattr(interface, operation)

            # Remove 'operation' and 'using' from kwargs
            op_kwargs = {k: v for k, v in kwargs.items()
                         if k not in ['operation', 'using']}

            # Execute the operation
            response = method(**op_kwargs)

            # Convert response to dict if needed
            if hasattr(response, "to_dict"):
                response = response.to_dict()

            return response

        except (BotoCoreError, ClientError) as e:
            error = ExecutionError(
                message=f"Failed to execute AWS operation: {e}",
                details={
                    "operation": operation,
                    "service": self.config.service.value,
                    "arguments": kwargs,
                },
            )
            self._logger.error("AWS operation error: %s", str(error))
            raise error from e

    def _disconnect_impl(self) -> None:
        """
        Implements disconnection logic for AWS.

        Raises:
            ConnectionError: If disconnection fails
        """
        try:
            # Close any open connections
            if self._client:
                self._client.close()

            # Clear references
            self._session = None
            self._client = None
            self._resource = None

        except Exception as e:
            error = ConnectionError(
                message=f"Failed to disconnect from AWS: {e}",
                details=self.config.get_info(),
            )
            self._logger.error("AWS disconnection error: %s", str(error))
            raise error from e

    def _test_connection(self) -> None:
        """Test connection by making a simple API call for the specific service."""
        try:
            service_test_methods = {
                AWSService.S3: self._client.list_buckets,
                AWSService.EC2: self._client.describe_regions,
                AWSService.RDS: self._client.describe_db_engine_versions,
                AWSService.IAM: self._client.list_account_aliases,
                # Add other service-specific test calls as needed
            }

            test_method = service_test_methods.get(self.config.service)
            if test_method:
                test_method()
            else:
                self._logger.warning(
                    "No connection test method for service %s",
                    self.config.service.value
                )

        except (BotoCoreError, ClientError) as e:
            raise ConnectionError(
                message=f"Connection test failed: {e}",
                details=self.config.get_info(),
            ) from e
