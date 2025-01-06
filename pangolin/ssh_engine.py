import paramiko
import logging
import time
from typing import Optional, Tuple
from pangolin.engine import Engine
from pangolin.exceptions import SSHConnectionError, SSHExecutionError


class SSH_Engine(Engine):
    """
    A robust and flexible SSH client SDK for remote server interactions.

    Features:
    - Supports both password and key-based authentication
    - Configurable connection and execution parameters
    - Comprehensive logging
    - Context manager support
    - Detailed error handling
    """

    def __init__(
        self,
        hostname: str,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        port: int = 22,
        **config,
    ):
        """
        Initialize the SSH client with connection parameters.

        Args:
            hostname (str): Hostname or IP address of the remote server
            username (str): Username for authentication
            password (Optional[str], optional): Password for authentication
            private_key (Optional[str], optional): Path to private key file
            port (int, optional): SSH port. Defaults to 22.
            **config: Additional configuration options
        """
        # Call parent's __init__ to set up configuration
        super().__init__(**config)

        # Connection parameters
        self.hostname = hostname
        self.username = username
        self.password = password
        self.private_key = private_key
        self.port = port

        # Logging setup
        self.logger = logging.getLogger(f"SSHClient_{hostname}")
        self.logger.setLevel(
            logging.DEBUG if self.config["logging_enabled"] else logging.ERROR
        )

        # Client state
        self._client = None
        self._last_command_result = None
        self._last_error = None

    def setup(self):
        """
        Establish the SSH connection.

        Raises:
            SSHConnectionError: If connection cannot be established
        """
        self._establish_connection()

    def _establish_connection(self):
        """
        Establish SSH connection with retry mechanism.

        Raises:
            SSHConnectionError: If connection cannot be established
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        for attempt in range(self.config["connection_retries"]):
            try:
                # Authenticate using private key if provided, else use password
                if self.private_key:
                    client.connect(
                        hostname=self.hostname,
                        username=self.username,
                        key_filename=self.private_key,
                        port=self.port,
                        timeout=self.config["timeout"],
                    )
                else:
                    client.connect(
                        hostname=self.hostname,
                        username=self.username,
                        password=self.password,
                        port=self.port,
                        timeout=self.config["timeout"],
                    )

                self._client = client
                self.logger.info(f"Connected to {self.hostname} successfully.")
                return

            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                self.logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                self._last_error = str(e)

                if attempt < self.config["connection_retries"] - 1:
                    time.sleep(1)
                else:
                    self.logger.error(f"Failed to connect to {self.hostname}")
                    raise SSHConnectionError(f"Authentication failed: {e}")

    def execute(
        self, command: str, raise_on_error: bool = True
    ) -> Tuple[str, str, int]:
        """
        Execute a command on the remote server.

        Args:
            command (str): Command to execute
            raise_on_error (bool, optional): Raise exception on non-zero exit status. Defaults to True.

        Returns:
            Tuple[str, str, int]: stdout, stderr, and exit status

        Raises:
            SSHExecutionError: If command execution fails and raise_on_error is True
        """
        if not self._client:
            raise SSHConnectionError("Not connected. Use connect() or setup() first.")

        self.logger.info(f"Executing command: {command}")

        try:
            stdin, stdout, stderr = self._client.exec_command(command)

            # Read outputs
            stdout_output = stdout.read().decode("utf-8").strip()
            stderr_output = stderr.read().decode("utf-8").strip()
            exit_status = stdout.channel.recv_exit_status()

            # Log results
            self.logger.debug(f"Command output: {stdout_output}")
            self.logger.debug(f"Command error: {stderr_output}")
            self.logger.debug(f"Exit status: {exit_status}")

            # Store last command result
            self._last_command_result = {
                "stdout": stdout_output,
                "stderr": stderr_output,
                "exit_status": exit_status,
            }

            # Optionally raise error for non-zero exit status
            if raise_on_error and exit_status != 0:
                self._last_error = stderr_output
                raise SSHExecutionError(
                    f"Command failed with exit status {exit_status}: {stderr_output}"
                )

            return stdout_output, stderr_output, exit_status

        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            self._last_error = str(e)
            raise SSHExecutionError(f"Failed to execute command: {e}")

    def result(self):
        """
        Return the result of the last executed command.

        Returns:
            str: stdout of the last command
        """
        if self._last_command_result:
            return self._last_command_result["stdout"]
        return ""

    def error(self):
        """
        Return the error of the last operation.

        Returns:
            str: Error message or stderr of the last command
        """
        return self._last_error or ""

    def disconnect(self):
        """
        Disconnect from the SSH server.
        """
        if self._client:
            self._client.close()
            self.logger.info(f"Disconnected from {self.hostname}")
            self._client = None

    def __del__(self):
        """
        Ensure connection is closed when object is deleted.
        """
        self.disconnect()


# Example usage
def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Create SSH client with custom configuration
        client = SSH_Engine(
            hostname="jarvis.local",
            username="jarvis",
            password="M@nish123",  # Or use private_key='path/to/key'
            timeout=15,  # Override default timeout
            connection_retries=2,  # Custom retry count
        )

        # Use context manager for connection
        client.setup()
        stdout, stderr, status = client.execute("ls -l")
        print(f"Output: {stdout}")
        client.execute("pwd")
        print(f"Last result: {client.result()}")

    except (SSHConnectionError, SSHExecutionError) as e:
        print(f"SSH Error: {e}")


if __name__ == "__main__":
    main()
