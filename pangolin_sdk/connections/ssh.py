"""SSH Connection implementation for the Pangolin SDK.

This module provides an SSHConnection class for establishing and managing
SSH connections with various authentication methods.
"""

from typing import Any, Tuple, Optional
import logging
import paramiko

from pangolin_sdk.configs.ssh import SSHAuthMethod, SSHConnectionConfig
from pangolin_sdk.connections.base import BaseConnection, T
from pangolin_sdk.constants import ConnectionStatus
from pangolin_sdk.exceptions import SSHConnectionError, SSHExecutionError


class SSHConnection(BaseConnection[Tuple[Any, Any]]):
    """Simple SSH connection implementation.

    Attributes:
        config (SSHConnectionConfig): Configuration for the SSH connection.
        _client (Optional[paramiko.SSHClient]): SSH client instance.
        stdin (Optional[Any]): Standard input stream.
        stdout (Optional[str]): Standard output stream.
        stderr (Optional[str]): Standard error stream.
    """

    def __init__(self, config: SSHConnectionConfig):
        """
        Initialize SSH connection.

        Args:
            config (SSHConnectionConfig): Configuration for the SSH connection.
        """
        self.config = config
        super().__init__(config)
        self._client: Optional[paramiko.SSHClient] = None
        self.stdin: Optional[Any] = None
        self.stdout: Optional[str] = None
        self.stderr: Optional[str] = None
        self._logger = self._setup_logger("paramiko")

    def _connect_impl(self) -> T:
        """
        Connect to the SSH server.

        Returns:
            T: Connected SSH client.

        Raises:
            SSHConnectionError: If connection fails.
        """
        try:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Authentication method selection
            auth_method_map = {
                SSHAuthMethod.PASSWORD: self._password_authentication,
                SSHAuthMethod.PUBLIC_KEY: self._public_key_authentication,
                SSHAuthMethod.AGENT: self._ssh_agent_authentication,
            }

            auth_func = auth_method_map.get(self.config.auth_method)
            if not auth_func:
                raise ValueError(
                    f"Unsupported authentication method: {self.config.auth_method}"
                )

            auth_func()
            self._logger.info(f"{self.config.auth_method} authentication successful!")
            return self._client
        except Exception as e:
            error = SSHConnectionError(
                message=f"SSH Connection Error: {e}", details=self.config.get_info()
            )
            self._logger.error(str(error))
            raise error

    def _password_authentication(self) -> None:
        """
        Authenticate using password.

        Raises:
            paramiko.AuthenticationException: If authentication fails.
        """
        self._client.connect(
            hostname=self.config.host,
            port=self.config.port,
            username=self.config.username,
            password=self.config.password,
            timeout=self.config.timeout,
        )

    def _public_key_authentication(self) -> None:
        """
        Authenticate using public key.

        Raises:
            paramiko.AuthenticationException: If authentication fails.
        """
        self._client.connect(
            hostname=self.config.host,
            port=self.config.port,
            username=self.config.username,
            pkey=self.config.private_key,
            timeout=self.config.timeout,
            passphrase=self.config.passphrase,
        )

    def _ssh_agent_authentication(self) -> None:
        """
        Authenticate using SSH agent.

        Raises:
            paramiko.AuthenticationException: If authentication fails.
        """
        self._client.connect(
            hostname=self.config.host,
            username=self.config.username,
            allow_agent=self.config.allow_agent,
            look_for_keys=self.config.look_for_keys,
        )

    def _execute_impl(self, *args: Any, **kwargs: Any) -> Optional[str]:
        """
        Execute a command on the SSH server.

        Args:
            *args: Positional arguments, first argument expected to be the command.
            **kwargs: Additional keyword arguments.

        Returns:
            Optional[str]: Standard output of the command.

        Raises:
            SSHExecutionError: If command execution fails.
        """
        if self.status != ConnectionStatus.CONNECTED:
            self.connect()

        try:
            if not args:
                raise ValueError("No command provided for execution")

            command = args[0]
            self._logger.info(f"Executing command: {command}")

            # Execute command and capture streams
            stdin, stdout, stderr = self._client.exec_command(command)

            # Read and decode streams
            stderr_output = stderr.read().decode("utf-8").strip()
            stdout_output = stdout.read().decode("utf-8").strip()

            # Store streams for potential later use
            self.stdin = stdin
            self.stdout = stdout_output
            self.stderr = stderr_output

            # Check for and handle errors
            if stderr_output:
                self._logger.error(f"Execution failed: {stderr_output}")
                raise SSHExecutionError(
                    message=f"SSH Execution Error: {stderr_output}",
                    details=self.config.get_info(),
                )

            return stdout_output

        except Exception as e:
            error = SSHExecutionError(
                message=f"SSH Execution Error: {e}", details=self.config.get_info()
            )
            raise error

    def _disconnect_impl(self) -> None:
        """
        Disconnect from the SSH server.

        Raises:
            SSHConnectionError: If disconnection fails.
        """
        try:
            if self._client:
                self._client.close()
        except Exception as e:
            error = SSHConnectionError(
                message=f"SSH Disconnection Error: {e}", details=self.config.get_info()
            )
            self._logger.error(str(error))
            raise error
