import datetime
from dataclasses import field, dataclass
from typing import Dict, Any


@dataclass(kw_only=True)
class ConnectionError(BaseException):
    """Base exception for all connection-related errors."""

    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.utcnow)

    def __str__(self):
        return f"{self.message} (Details: {self.details}, Timestamp: {self.timestamp})"


@dataclass(kw_only=True)
class DatabaseConnectionError(ConnectionError):
    """
    Exception raised for database connection errors.

    Attributes:
        message (str): Detailed error description
        connection_params (dict, optional): Connection parameters
    """

    connection_params: Dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class APIConnectionError(ConnectionError):
    """
    Exception raised for API connection errors.

    Attributes:
        message (str): Detailed error description
        status_code (int, optional): HTTP status code if applicable
    """

    status_code: int = None


@dataclass(kw_only=True)
class AuthError(ConnectionError):
    """
    Exception raised for authentication errors.

    Attributes:
        message (str): Detailed error description
        status_code (int, optional): HTTP status code if applicable
    """

    status_code: int = None


@dataclass(kw_only=True)
class ExecutionError(ConnectionError):
    """
    Exception raised for execution errors.

    Attributes:
        message (str): Detailed error description
    """

    pass


@dataclass(kw_only=True)
class APIExecutionError(ExecutionError):
    """
    Exception raised for API request execution errors.

    Attributes:
        message (str): Detailed error description
        status_code (int, optional): HTTP status code if applicable
        response (dict, optional): Full response details
    """

    status_code: int = None
    response: Dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class DatabaseQueryError(ExecutionError):
    """
    Exception raised for database query execution errors.

    Attributes:
        message (str): Detailed error description
        query (str, optional): The query that caused the error
        params (dict, optional): Query parameters
    """

    query: str = None
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class SSHConnectionError(ConnectionError):
    """
    Exception raised for SSH connection errors.

    Attributes:
        message (str): Detailed error description
        hostname (str, optional): Target hostname
        username (str, optional): Username used for connection
    """

    hostname: str = None
    username: str = None


@dataclass(kw_only=True)
class SSHExecutionError(ExecutionError):
    """
    Exception raised for SSH execution errors.

    Attributes:
        message (str): Detailed error description
        command (str, optional): The command that caused the error
    """

    command: str = None


#
