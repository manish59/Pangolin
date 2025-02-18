"""Custom exception classes for connection, authentication, and execution errors.

This module provides a comprehensive set of exception classes to handle
various error scenarios in connection and execution contexts.
"""

import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(kw_only=True)
class BaseConnectionError(BaseException):
    """Base exception for all connection-related errors.

    Attributes:
        message (str): Detailed error description
        details (dict, optional): Additional error details
        timestamp (datetime): Timestamp of the error occurrence
    """

    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.utcnow)

    def __str__(self) -> str:
        """
        Create a string representation of the error.

        Returns:
            str: Formatted error message with details and timestamp
        """
        return (
            f"{self.message} " f"(Details: {self.details}, Timestamp: {self.timestamp})"
        )


@dataclass(kw_only=True)
class DatabaseConnectionError(BaseConnectionError):
    """
    Exception raised for database connection errors.

    Attributes:
        message (str): Detailed error description
        connection_params (dict, optional): Connection parameters
    """

    connection_params: Dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class APIConnectionError(BaseConnectionError):
    """
    Exception raised for API connection errors.

    Attributes:
        message (str): Detailed error description
        status_code (int, optional): HTTP status code if applicable
    """

    status_code: Optional[int] = None


@dataclass(kw_only=True)
class AuthError(BaseConnectionError):
    """
    Exception raised for authentication errors.

    Attributes:
        message (str): Detailed error description
        status_code (int, optional): HTTP status code if applicable
    """

    status_code: Optional[int] = None


@dataclass(kw_only=True)
class BaseExecutionError(BaseConnectionError):
    """
    Exception raised for execution errors.

    Attributes:
        message (str): Detailed error description
    """


@dataclass(kw_only=True)
class APIExecutionError(BaseExecutionError):
    """
    Exception raised for API request execution errors.

    Attributes:
        message (str): Detailed error description
        status_code (int, optional): HTTP status code if applicable
        response (dict, optional): Full response details
    """

    status_code: Optional[int] = None
    response: Dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class DatabaseQueryError(BaseExecutionError):
    """
    Exception raised for database query execution errors.

    Attributes:
        message (str): Detailed error description
        query (str, optional): The query that caused the error
        params (dict, optional): Query parameters
    """

    query: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class SSHConnectionError(BaseConnectionError):
    """
    Exception raised for SSH connection errors.

    Attributes:
        message (str): Detailed error description
        hostname (str, optional): Target hostname
        username (str, optional): Username used for connection
    """

    hostname: Optional[str] = None
    username: Optional[str] = None


@dataclass(kw_only=True)
class SSHExecutionError(BaseExecutionError):
    """
    Exception raised for SSH execution errors.

    Attributes:
        message (str): Detailed error description
        command (str, optional): The command that caused the error
    """

    command: Optional[str] = None
