class PangolinError(Exception):
    """Base exception for all Pangolin SDK errors."""

    pass


class ConnectionError(PangolinError):
    """Base class for connection-related errors."""

    pass


class ExecutionError(PangolinError):
    """Base class for execution-related errors."""

    pass


class APIConnectionError(ConnectionError):
    """
    Exception raised for API connection errors.

    Attributes:
        message (str): Detailed error description
        status_code (int, optional): HTTP status code if applicable
    """

    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class APIExecutionError(ExecutionError):
    """
    Exception raised for API request execution errors.

    Attributes:
        message (str): Detailed error description
        status_code (int, optional): HTTP status code if applicable
        response (dict, optional): Full response details
    """

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class DatabaseConnectionError(ConnectionError):
    """
    Exception raised for database connection errors.

    Attributes:
        message (str): Detailed error description
        connection_params (dict, optional): Connection parameters
    """

    def __init__(self, message: str, connection_params: dict = None):
        self.message = message
        self.connection_params = connection_params
        super().__init__(self.message)


class DatabaseQueryError(ExecutionError):
    """
    Exception raised for database query execution errors.

    Attributes:
        message (str): Detailed error description
        query (str, optional): The query that caused the error
        params (dict, optional): Query parameters
    """

    def __init__(self, message: str, query: str = None, params: dict = None):
        self.message = message
        self.query = query
        self.params = params
        super().__init__(self.message)


class SSHConnectionError(ConnectionError):
    """
    Exception raised for SSH connection errors.

    Attributes:
        message (str): Detailed error description
        hostname (str, optional): Target hostname
        username (str, optional): Username used for connection
    """

    def __init__(self, message: str, hostname: str = None, username: str = None):
        self.message = message
        self.hostname = hostname
        self.username = username
        super().__init__(self.message)


class SSHExecutionError(ExecutionError):
    """
    Exception raised for SSH command execution errors.

    Attributes:
        message (str): Detailed error description
        command (str, optional): Command that failed
        exit_status (int, optional): Command exit status
    """

    def __init__(self, message: str, command: str = None, exit_status: int = None):
        self.message = message
        self.command = command
        self.exit_status = exit_status
        super().__init__(self.message)
