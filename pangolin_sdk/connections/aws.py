from typing import Any, Dict, Optional
import boto3
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError

from pangolin_sdk.connections.base import BaseConnection
from pangolin_sdk.configs.aws import AWSConnectionConfig
from pangolin_sdk.constants import AWSAuthMethod, ConnectionStatus, AWSService
from pangolin_sdk.exceptions import ConnectionError, ExecutionError


class AWSConnection(BaseConnection[BaseClient]):
    """Implementation of AWS connection handling."""

    def __init__(self, config: AWSConnectionConfig):
        """Initialize AWS connection."""
        super().__init__(config)
        self.config = config
        self._session = None
        self._client = None
        self._resource = None

    def _connect_impl(self) -> BaseClient:
        """
        Implements connection logic for AWS.

        Returns:
            botocore.client.BaseClient: AWS service client

        Raises:
            ConnectionError: If connection fails
        """
        try:
            kwargs = {"region_name": self.config.region.value}

            if self.config.endpoint_url:
                kwargs["endpoint_url"] = self.config.endpoint_url

            if self.config.verify_ssl is not None:
                kwargs["verify"] = self.config.verify_ssl

            if self.config.api_version:
                kwargs["api_version"] = self.config.api_version

            # Create session based on authentication method
            if self.config.auth_method == AWSAuthMethod.ACCESS_KEY:
                session = boto3.Session(
                    aws_access_key_id=self.config.access_key_id,
                    aws_secret_access_key=self.config.secret_access_key,
                    aws_session_token=self.config.session_token,
                )

            elif self.config.auth_method == AWSAuthMethod.PROFILE:
                session = boto3.Session(
                    profile_name=self.config.profile_name,
                )

            elif self.config.auth_method == AWSAuthMethod.INSTANCE_ROLE:
                session = boto3.Session()

            elif self.config.auth_method == AWSAuthMethod.WEB_IDENTITY:
                session = boto3.Session()
                # Web identity is handled by AWS SDK using environment variables:
                # AWS_ROLE_ARN, AWS_WEB_IDENTITY_TOKEN_FILE

            elif self.config.auth_method == AWSAuthMethod.SSO:
                session = boto3.Session(
                    profile_name=self.config.profile_name,
                )
                # SSO authentication is handled through AWS CLI SSO login

            else:
                raise ValueError(
                    f"Unsupported authentication method: {self.config.auth_method}"
                )

            # Store session
            self._session = session

            # Create service client
            self._client = session.client(self.config.service.value, **kwargs)

            # Optionally create service resource
            try:
                self._resource = session.resource(self.config.service.value, **kwargs)
            except Exception:
                # Not all services have resource interface
                self._resource = None

            # Test connection by making a simple API call
            self._test_connection()

            return self._client

        except (BotoCoreError, ClientError) as e:
            error = ConnectionError(
                message=f"Failed to connect to AWS: {str(e)}",
                details=self.config.get_info(),
            )
            raise error

    def _execute_impl(
        self, operation: str, using: str = "client", **kwargs
    ) -> Dict[str, Any]:
        """
        Execute AWS operations.

        Args:
            operation: The AWS API operation to perform
            using: Use 'client' or 'resource' interface (default: client)
            **kwargs: Additional arguments for the operation

        Returns:
            Dict containing operation results

        Raises:
            ExecutionError: If execution fails
        """
        try:
            # Choose interface
            interface = self._client if using == "client" else self._resource
            if not interface:
                raise ValueError(f"AWS {using} interface not available")

            # Get the operation method
            method = getattr(interface, operation)
            if not method:
                raise ValueError(
                    f"Operation {operation} not found on {using} interface"
                )

            # Execute the operation
            response = method(**kwargs)

            # Convert response to dict if needed
            if hasattr(response, "to_dict"):
                response = response.to_dict()

            return response

        except (BotoCoreError, ClientError) as e:
            error = ExecutionError(
                message=f"Failed to execute AWS operation: {str(e)}",
                details={
                    "operation": operation,
                    "service": self.config.service.value,
                    "arguments": kwargs,
                },
            )
            raise error

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
                message=f"Failed to disconnect from AWS: {str(e)}",
                details=self.config.get_info(),
            )
            raise error

    def _test_connection(self) -> None:
        """Test connection by making a simple API call."""
        try:
            if self.config.service == AWSService.S3:
                self._client.list_buckets()
            elif self.config.service == AWSService.EC2:
                self._client.describe_regions()
            elif self.config.service == AWSService.RDS:
                self._client.describe_db_engine_versions()
            elif self.config.service == AWSService.IAM:
                self._client.list_account_aliases()
            # Add other service-specific test calls as needed

        except (BotoCoreError, ClientError) as e:
            raise ConnectionError(
                message=f"Connection test failed: {str(e)}",
                details=self.config.get_info(),
            )
