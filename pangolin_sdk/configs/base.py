"""
This module contains base configuration classes for connections.
"""
from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass(kw_only=True)
class BaseConfig:
    """Base configuration for connections."""

    name: str
    host: str
    timeout: int = 30
    max_retries: int = 3
    retry_interval: int = 5
    retry_backoff: float = 1.5

    def get_info(self):
        """Converts the dataclass to a dictionary and prints it."""
        return asdict(self)


@dataclass(kw_only=True)
class ConnectionConfig(BaseConfig):
    """Configuration for a connection with additional parameters."""

    username: Optional[str] = None
    password: Optional[str] = None
    retry_jitter: bool = True
    ssl_enabled: bool = True
    ssl_verify: bool = True
    options: dict = field(default_factory=dict)

    def __post_init__(self):
        pass
