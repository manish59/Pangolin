# We will implement the SSHConnection class here
from typing import Any, Tuple

import paramiko

from pangolin_sdk.configs.ssh import SSHAuthMethod, SSHConnectionConfig
from pangolin_sdk.connections.base import BaseConnection, T
from pangolin_sdk.constants import ConnectionStatus
from pangolin_sdk.exceptions import SSHConnectionError, SSHExecutionError


class SSHConnection(BaseConnection[Tuple[Any, Any]]):
    """Simple SSH connection implementation."""

    def __init__(self, config: SSHConnectionConfig):
        """Initialize database connection."""
        self.config = config
        super().__init__(config)
        self._client = None
        self.stdin = None
        self.stdout = None
        self.stderr = None
        self._logger = self._setup_logger("paramiko")

    def _connect_impl(self) -> T:
        """Connect to the SSH server."""
        try:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.config.auth_method == SSHAuthMethod.PASSWORD:
                self._password_authentication()
            elif self.config.auth_method == "publickey":
                self._public_key_authentication()
            elif self.config.auth_method == "agent":
                self._ssh_agent_authentication()
            else:
                raise ValueError(
                    f"Unsupported authentication method: {self.config.auth_method}"
                )
            print(f"{self.config.auth_method} authentication successful!")
            return self._client
        except Exception as e:
            error = SSHConnectionError(
                message=f"SSH Connection Error {e}", details=self.config.get_info()
            )
            raise error

    def _password_authentication(self):
        """Authenticate using password."""
        self._client.connect(
            self.config.host,
            port=self.config.port,
            username=self.config.username,
            password=self.config.password,
            timeout=self.config.timeout,
        )

    def _public_key_authentication(self):
        """Authenticate using public key."""

        self._client.connect(
            self.config.host,
            port=self.config.port,
            username=self.config.username,
            pkey=self.config.pkey,
            timeout=self.config.timeout,
        )

    def _ssh_agent_authentication(self):
        """Authenticate using SSH agent."""
        self._client.connect(
            hostname=self.config.host,
            username=self.config.username,
            allow_agent=self.config.allow_agent,
            look_for_keys=self.config.look_for_keys,
        )

    def _execute_impl(self, *args, **kwargs) -> None:
        """Execute a connection request."""
        if self.status != ConnectionStatus.CONNECTED:
            self.connect()
        try:
            command = args[0]
            self._logger.info(f"Executing command: {command}")
            self.stdin, self.stdout, self.stderr = self._client.exec_command(
                command)
            self.stderr = self.stderr.read().decode("utf-8")
            self.stdout = self.stdout.read().decode("utf-8")
            if self.stderr:
                self._logger.error(f"Execution failed: {self.stderr}")
                raise SSHExecutionError(
                    message=f"SSH Execution Error {self.stderr}",
                    details=self.config.get_info(),
                )
            else:
                self._logger.info(f"Execution performed successfully")
                return self.stdout
        except Exception as e:
            error = SSHExecutionError(
                message=f"SSH Execution Error {e}", details=self.config.get_info()
            )
            self._logger.error(f"Execution failed: {str(e)}")
            raise error

    def _disconnect_impl(self) -> None:
        """Disconnect from the SSH server."""
        try:
            self._client.close()
        except Exception as e:
            raise SSHConnectionError(
                message=f"SSH Disconnection Error {e}", details=self.config.get_info()
            )
