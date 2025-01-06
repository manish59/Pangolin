class SSHConnectionError(Exception):
    """Custom exception for SSH connection errors."""

    pass


class SSHExecutionError(Exception):
    """Custom exception for SSH command execution errors."""

    pass


class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors."""
    pass


class DatabaseQueryError(Exception):
    """Custom exception for database query execution errors."""
    pass
