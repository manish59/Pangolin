"""Database configuration module for Pangolin SDK.

This module provides configuration classes for database connections,
supporting various database types and connection methods.
"""

from dataclasses import dataclass
from typing import List, Optional, Any

from pangolin_sdk.configs.base import ConnectionConfig
from pangolin_sdk.constants import DatabaseType


@dataclass(kw_only=True)
class DatabaseConnectionConfig(ConnectionConfig):
    """Database-specific connection configuration.

    This class extends the base ConnectionConfig with database-specific
    parameters and validation logic.

    Attributes:
        database_type: Type of database (PostgreSQL, Oracle, etc.)
        connection_string: Full database connection string
        port: Database server port
        database: Database name
        service_name: Oracle service name
        sid: Oracle system identifier
        tns_name: Oracle TNS name
        schema: Database schema
    """

    database_type: DatabaseType = DatabaseType.POSTGRESQL
    connection_string: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    service_name: Optional[str] = None
    sid: Optional[str] = None
    tns_name: Optional[str] = None
    schema: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate database configuration after initialization.

        Raises:
            ValueError: If required connection parameters are missing
        """
        if not self.connection_string:
            self._validate_db_specific_config()

    def _validate_db_specific_config(self) -> None:
        """Validate database-specific configuration parameters.

        Raises:
            ValueError: If required parameters for the specific database type are missing
        """
        if self.database_type == DatabaseType.ORACLE:
            self._validate_oracle_config()
        else:
            self._validate_standard_config()

    def _validate_oracle_config(self) -> None:
        """Validate Oracle-specific configuration.

        Raises:
            ValueError: If required Oracle connection parameters are missing
        """
        has_tns = bool(self.tns_name)
        has_host_port = bool(self.host and self.port)
        has_service_identifiers = bool(self.service_name or self.sid or self.database)

        if not (has_tns or (has_host_port and has_service_identifiers)):
            raise ValueError(
                "Oracle connection requires either connection_string, tns_name, "
                "or host/port/service_name (or SID)"
            )

    def _validate_standard_config(self) -> None:
        """Validate standard database configuration.

        Raises:
            ValueError: If required connection parameters are missing
        """
        self._handle_postgres_timeout()

        required_params = self._get_required_params()
        if not all(required_params):
            missing_params = self._get_missing_param_names(required_params)
            raise ValueError(
                f"Database connection requires the following parameters: {', '.join(missing_params)}"
            )

    def _handle_postgres_timeout(self) -> None:
        """Handle PostgreSQL-specific timeout configuration."""
        if (
            self.database_type == DatabaseType.ORACLE
            or self.database_type == DatabaseType.MSSQL
        ):
            self.options["timeout"] = self.timeout
        else:
            self.options["connect_timeout"] = self.timeout

    def _get_required_params(self) -> List[Any]:
        """Get list of required parameters for validation.

        Returns:
            List of parameter values to validate
        """
        return [
            self.host,
            self.port,
            self.database,
            self.username,
            self.password,
        ]

    def _get_missing_param_names(self, params: List[Any]) -> List[str]:
        """Get names of missing required parameters.

        Args:
            params: List of parameter values to check

        Returns:
            List of parameter names that are missing or None
        """
        param_names = ["host", "port", "database", "username", "password"]
        return [name for name, value in zip(param_names, params) if not value]
