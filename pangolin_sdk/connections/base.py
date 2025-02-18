"""Base Connection Module for Pangolin SDK."""

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
from pangolin_sdk.exceptions import ConnectionError, ExecutionError

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
    """Abstract base class for all connection types."""

    def __init__(self, config: ConnectionConfig):
        """Initialize the base connection."""
        self.connection_id = str(uuid.uuid4())
        self.config = config
        self.status = ConnectionStatus.INITIALIZED
        self.metrics = ConnectionMetrics()
        self.errors: List[Any] = []
        self._logger = self._setup_logger()
        self.results: List[Any] = []
        self._last_error = None
        self._last_result = None

    def _setup_logger(self, *args, **kwargs) -> logging.Logger:
        """Set up logging for the connection."""
        logger = None
        if args:
            logger = logging.getLogger(f"{args[0]}")
        logger = logging.getLogger(f"pangolin.connection.{self.config.name}")
        logger.setLevel(logging.INFO)
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
            T: Connection object specific to the implementation
        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    def _disconnect_impl(self) -> None:
        """Implementation specific disconnection logic.

        Raises:
            ConnectionError: If disconnection fails
        """
        pass

    @abstractmethod
    def _execute_impl(self, *args, **kwargs) -> None:
        """Implementation specific execution logic.

        Raises:
            ExecutionError: If execution fails
        """
        pass

    def connect(self) -> Optional[T]:
        """Establish connection with retry logic."""
        if self.status == ConnectionStatus.CONNECTED and self._connection is not None:
            return self._connection

        self.status = ConnectionStatus.CONNECTING
        retry_count = 0
        last_error = None

        while retry_count <= self.config.max_retries:
            try:
                self._logger.info(
                    f"Attempting connection {retry_count + 1}/{self.config.max_retries + 1}"
                )
                start_time = datetime.utcnow()

                # Attempt to establish connection
                _connection = self._connect_impl()

                if _connection is not None:
                    self.status = ConnectionStatus.CONNECTED
                    self.metrics.last_connected_at = datetime.utcnow()
                    self.metrics.total_connections += 1
                    connection_time = (datetime.utcnow() -
                                       start_time).total_seconds()
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
                        f"Connection failed, retrying in {retry_delay}s: {str(e)}"
                    )
                    time.sleep(retry_delay)

                retry_count += 1
                self.metrics.total_retries += 1

        self.status = ConnectionStatus.ERROR
        self._logger.error(
            f"Connection failed after {retry_count} retries: {str(last_error)}"
        )
        return None

    def execute(self, *args, **kwargs) -> None:
        """Execute a connection request."""
        if self.status != ConnectionStatus.CONNECTED:
            self.connect()
        try:
            result = self._execute_impl(*args, **kwargs)
            self.results.append(result)
            self._last_result = result
            self._logger.info(f"Execution performed successfully")
        except ExecutionError as e:
            self.metrics.total_errors += 1
            self._record_error(e)
            self._logger.error(f"Execution failed: {str(e)}")
            self.disconnect()

    def disconnect(self) -> None:
        """Disconnect from the resource."""
        self._logger.info(f"Disconnecting from the database...")
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
            self._logger.error(f"Disconnection failed: {str(e)}")

    def get_connection(self) -> Optional[T]:
        """Get the current connection object."""
        return self._connection

    def _calculate_retry_delay(self, retry_count: int) -> float:
        """Calculate delay for next retry attempt."""
        delay = self.config.retry_interval * \
            (self.config.retry_backoff**retry_count)
        if self.config.retry_jitter:
            delay *= 0.5 + random.random()
        return delay

    def _update_avg_connection_time(self, new_time: float) -> None:
        """Update the average connection time metric."""
        current_avg = self.metrics.avg_connection_time
        total_connections = self.metrics.total_connections
        self.metrics.avg_connection_time = (
            current_avg * (total_connections - 1) + new_time
        ) / total_connections

    def _record_error(self, error: ConnectionError) -> None:
        """Record an error occurrence."""
        self.errors.append(error)
        self.metrics.last_error_at = error.timestamp

    def get_status(self) -> ConnectionStatus:
        """Get current connection status."""
        return self.status

    def get_metrics(self) -> ConnectionMetrics:
        """Get connection metrics."""
        return self.metrics

    def get_errors(self) -> List[ConnectionError]:
        """Get recorded errors."""
        return self.errors

    def get_last_result(self) -> Any:
        """Get the result of"""
        return self._last_result

    def get_results(self) -> List[Any]:
        """Get all results."""
        return self.results

    def get_info(self) -> Dict[str, Any]:
        """Get comprehensive connection information."""
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
