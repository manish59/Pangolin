from dataclasses import dataclass
from typing import Optional

from pangolin_sdk.configs.base import ConnectionConfig
from pangolin_sdk.constants import DatabaseType


@dataclass(kw_only=True)
class DatabaseConnectionConfig(ConnectionConfig):
    """Database-specific connection configuration."""

    database_type: DatabaseType = DatabaseType.POSTGRESQL
    connection_string: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    service_name: Optional[str] = None
    sid: Optional[str] = None
    tns_name: Optional[str] = None
    schema: Optional[str] = None

    def __post_init__(self):
        """Validate configuration."""
        required_params = []
        if not self.connection_string:
            if self.database_type == DatabaseType.ORACLE:
                # Oracle needs either connection_string, tns_name, or host+port+(service_name|sid)
                if not (
                    self.tns_name
                    or (
                        self.host
                        and self.port
                        and (self.service_name or self.sid or self.database)
                    )
                ):
                    raise ValueError(
                        "Oracle connection requires either connection_string, tns_name, "
                        "or host/port/service_name (or SID)"
                    )
            if self.database_type == DatabaseType.POSTGRESQL:
                if "tcp_connect_timeout" in self.options:
                    self.options["timeout"] = self.options.pop(
                        "tcp_connect_timeout")
                required_params = [
                    self.host,
                    self.port,
                    self.database,
                    self.username,
                    self.password,
                ]
            else:
                # Other databases need all standard parameters
                required_params = [
                    self.host,
                    self.port,
                    self.database,
                    self.username,
                    self.password,
                ]
        if not all(required_params):
            raise ValueError(
                "Database connection requires host, port, database, username, and password"
            )
