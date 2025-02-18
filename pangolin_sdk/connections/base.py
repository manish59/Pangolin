"""Base Connection Module for Pangolin SDK.

This module provides a base connection framework with robust error handling,
connection management, and performance metrics tracking.
"""

import logging
import random
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pangolin_sdk.configs.base import ConnectionConfig
from pangolin_sdk.constants import ConnectionStatus
from pangolin_sdk.exceptions import (
    BaseConnectionError as ConnectionError,
    BaseExecutionError as ExecutionError,
)

# Generic type for connection objects
T = TypeVar("T")


@dataclass
class ConnectionMetrics:
    """Metrics for monitoring connection health and performance."""

    total_connections: int = 0
    failed_connections: int = 0
    total_disconnections: int = 0
    total_errors: int = 0
    total_retries: int = 0
    last_connected_at: Optional[datetime] = None
    last_disconnected_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    avg_connection_time: float = 0.0


class BaseConnection(ABC, Generic[T]):
    """Abstract base class for all connection types.

    Provides a standardized interface for connection management with built-in
    retry logic, error tracking, and performance metrics.
    """

    def __init__(self, config: ConnectionConfig) -> None:
        """Initialize the base connection.

        Args:
            config (ConnectionConfig): Configuration for the connection.
        """
        self.connection_id: str = str(uuid.uuid4())
        self.config: ConnectionConfig = config
        self.status: ConnectionStatus = ConnectionStatus.INITIALIZED
        self.metrics: ConnectionMetrics = ConnectionMetrics()
        self.errors: List[Any] = []
        self._logger: logging.Logger = self._setup_logger()
        self.results: List[Any] = []
        self._last_error: Optional[Any] = None
        self._last_result: Optional[Any] = None
        self._connection: Optional[T] = None

    def _setup_logger(self, *args: Any) -> logging.Logger:
        """Set up logging for the connection.

        Args:
            *args: Optional logger name arguments.
            **kwargs: Additional logging configuration.

        Returns:
            logging.Logger: Configured logger instance.
        """
        if args:
            logger_name = args[0]
        else:
            logger_name = f"pangolin.connection.{self.config.name}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        # Prevent adding multiple handlers
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    @abstractmethod
    def _connect_impl(self) -> T:
        """Implementation specific connection logic.

        Returns:
            T: Connection object specific to the implementation.

        Raises:
            ConnectionError: If connection fails.
        """
        raise NotImplementedError("Subclasses must implement connection logic")

    @abstractmethod
    def _disconnect_impl(self) -> None:
        """Implementation specific disconnection logic.

        Raises:
            ConnectionError: If disconnection fails.
        """
        raise NotImplementedError("Subclasses must implement disconnection logic")

    @abstractmethod
    def _execute_impl(self, *args: Any, **kwargs: Any) -> Any:
        """Implementation specific execution logic.

        Args:
            *args: Positional arguments for execution.
            **kwargs: Keyword arguments for execution.

        Raises:
            ExecutionError: If execution fails.

        Returns:
            Any: Result of the execution.
        """
        raise NotImplementedError("Subclasses must implement execution logic")

    def connect(self) -> Optional[T]:
        """Establish connection with retry logic.

        Returns:
            Optional[T]: Established connection object or None if failed.
        """
        if self.status == ConnectionStatus.CONNECTED and self._connection is not None:
            return self._connection

        self.status = ConnectionStatus.CONNECTING
        retry_count = 0
        last_error: Optional[ConnectionError] = None

        while retry_count <= self.config.max_retries:
            try:
                self._logger.info(
                    "Attempting connection %d/%d",
                    retry_count + 1,
                    self.config.max_retries + 1
                )
                start_time = datetime.utcnow()

                # Attempt to establish connection
                _connection = self._connect_impl()

                if _connection is not None:
                    self.status = ConnectionStatus.CONNECTED
                    self._connection = _connection
                    self.metrics.last_connected_at = datetime.utcnow()
                    self.metrics.total_connections += 1
                    connection_time = (datetime.utcnow() - start_time).total_seconds()
                    self._update_avg_connection_time(connection_time)
                    self._logger.info("Connection established successfully")
                    return _connection

            except ConnectionError as e:
                last_error = e
                self.metrics.failed_connections += 1
                self.metrics.total_errors += 1
                self._record_error(e)

                if retry_count < self.config.max_retries:
                    retry_delay = self._calculate_retry_delay(retry_count)
                    self._logger.warning(
                        "Connection failed, retrying in %0.2fs: %s",
                        retry_delay,
                        str(e)
                    )
                    time.sleep(retry_delay)

                retry_count += 1
                self.metrics.total_retries += 1

        self.status = ConnectionStatus.ERROR
        error_message = f"Connection failed after {retry_count} retries"
        if last_error:
            error_message += f": {str(last_error)}"
        self._logger.error(error_message)
        return None

    def execute(self, *args: Any, **kwargs: Any) -> None:
        """Execute a connection request.

        Args:
            *args: Positional arguments for execution.
            **kwargs: Keyword arguments for execution.
        """
        if self.status != ConnectionStatus.CONNECTED:
            self.connect()

        try:
            result = self._execute_impl(*args, **kwargs)
            self.results.append(result)
            self._last_result = result
            self._logger.info("Execution performed successfully")
        except ExecutionError as e:
            self.metrics.total_errors += 1
            self._record_error(e)
            self._logger.error("Execution failed: %s", str(e))
            self.disconnect()

    def disconnect(self) -> None:
        """Disconnect from the resource."""
        self._logger.info("Disconnecting from the resource...")

        if self.status == ConnectionStatus.DISCONNECTED:
            return

        self.status = ConnectionStatus.DISCONNECTING
        try:
            self._disconnect_impl()
            self.status = ConnectionStatus.DISCONNECTED
            self.metrics.last_disconnected_at = datetime.utcnow()
            self.metrics.total_disconnections += 1
            self._connection = None
            self._logger.info("Disconnected successfully")

        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.metrics.total_errors += 1
            self._record_error(e)
            self._logger.error("Disconnection failed: %s", str(e))

    def get_connection(self) -> Optional[T]:
        """Get the current connection object.

        Returns:
            Optional[T]: Current connection object.
        """
        return self._connection

    def _calculate_retry_delay(self, retry_count: int) -> float:
        """Calculate delay for next retry attempt.

        Args:
            retry_count (int): Current retry attempt number.

        Returns:
            float: Calculated retry delay.
        """
        delay = self.config.retry_interval * (self.config.retry_backoff**retry_count)
        if self.config.retry_jitter:
            delay *= 0.5 + random.random()
        return delay

    def _update_avg_connection_time(self, new_time: float) -> None:
        """Update the average connection time metric.

        Args:
            new_time (float): Most recent connection time.
        """
        current_avg = self.metrics.avg_connection_time
        total_connections = self.metrics.total_connections
        self.metrics.avg_connection_time = (
            current_avg * (total_connections - 1) + new_time
        ) / total_connections

    def _record_error(self, error: Any) -> None:
        """Record an error occurrence.

        Args:
            error (Any): Error to be recorded.
        """
        self.errors.append(error)
        # Use a custom timestamp if the error doesn't have a timestamp attribute
        self.metrics.last_error_at = (
            getattr(error, 'timestamp', datetime.utcnow())
        )

    def get_status(self) -> ConnectionStatus:
        """Get current connection status.

        Returns:
            ConnectionStatus: Current status of the connection.
        """
        return self.status

    def get_metrics(self) -> ConnectionMetrics:
        """Get connection metrics.

        Returns:
            ConnectionMetrics: Performance and health metrics.
        """
        return self.metrics

    def get_errors(self) -> List[Any]:
        """Get recorded errors.

        Returns:
            List[Any]: List of recorded errors.
        """
        return self.errors

    def get_last_result(self) -> Optional[Any]:
        """Get the most recent result.

        Returns:
            Optional[Any]: Most recent execution result.
        """
        return self._last_result

    def get_results(self) -> List[Any]:
        """Get all execution results.

        Returns:
            List[Any]: List of all execution results.
        """
        return self.results

    def get_info(self) -> Dict[str, Any]:
        """Get comprehensive connection information.

        Returns:
            Dict[str, Any]: Detailed connection information.
        """
        return {
            "connection_id": self.connection_id,
            "name": self.config.name,
            "status": self.status.value,
            "connected": self._connection is not None,
            "metrics": {
                "total_connections": self.metrics.total_connections,
                "failed_connections": self.metrics.failed_connections,
                "total_errors": self.metrics.total_errors,
                "total_retries": self.metrics.total_retries,
                "avg_connection_time": self.metrics.avg_connection_time,
                "last_connected": self.metrics.last_connected_at,
                "last_error": self.metrics.last_error_at,
            },
            "config": {
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries,
                "retry_interval": self.config.retry_interval,
                "ssl_enabled": self.config.ssl_enabled,
            },
        }
