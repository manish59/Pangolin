import logging
from abc import ABC, abstractmethod
from pangolin.config import PangolinConfig


class Engine(ABC):
    """Abstract base class for the SDK Engine."""

    def __init__(self, **config):
        """
        Initialize the Engine with optional configurations.

        Parameters:
            config (dict): Instance-specific configurations.
        """
        self.config = {
            "timeout": PangolinConfig.DEFAULT_TIMEOUT,
            "logging_enabled": PangolinConfig.LOGGING_ENABLED,
            "connection_retries": PangolinConfig.CONNECTION_RETRIES,
        }

        # Logging setup
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.logger.setLevel(
            logging.INFO if self.config["logging_enabled"] else logging.ERROR
        )

        # Connection and query state
        self._connection = None
        self._cursor = None
        self._last_query_result = None
        self._last_error = None

    def update_config(self, **kwargs):
        """
        Update the configuration for this Engine instance.

        Parameters:
            kwargs: Key-value pairs of configuration options to override.
        """
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
            else:
                raise KeyError(f"Invalid configuration option: {key}")

    @abstractmethod
    def setup(self):
        """Abstract method for setup logic. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def execute(self):
        """Abstract method for execution logic. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def result(self):
        """Abstract method for returning results. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def error(self):
        """Abstract method for error handling. Must be implemented by subclasses."""
        pass
