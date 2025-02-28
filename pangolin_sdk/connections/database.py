"""Simple Database Connection Implementation for Pangolin SDK."""

from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from pangolin_sdk.configs.database import DatabaseConnectionConfig
from pangolin_sdk.connections.base import BaseConnection
from pangolin_sdk.exceptions import DatabaseConnectionError, DatabaseQueryError


class DatabaseConnection(BaseConnection[Tuple[Any, Any]]):
    """Simple database connection implementation."""

    def __init__(self, config: DatabaseConnectionConfig):
        """Initialize database connection."""
        self.config = config
        super().__init__(config)
        self._db_module = None
        self._engine = None
        self._session = None
        self.encode_username = False
        self.encode_password = False

    def _encode_credentials(
        self,
    ):
        if self.encode_username is False:
            self.config.username = quote_plus(self.config.username)
        if self.encode_password is False:
            self.config.password = quote_plus(self.config.password)

    def _get_connection_string(self) -> str:
        """
        Generate connection string based on database type.

        Returns:
            str: Database connection string

        Raises:
            ValueError: If database type is unsupported
        """
        # Connection string generators for different databases
        connection_strings = {
            "sqlite": self._get_sqlite_connection_string,
            "postgresql": self._get_postgresql_connection_string,
            "mysql": self._get_mysql_connection_string,
            "oracle": self._get_oracle_connection_string,
            "mssql": self._get_mssql_connection_string,
        }

        # Get and validate connection string generator
        if self.config.database_type.value not in connection_strings:
            raise ValueError(f"Unsupported database type: {self.config.database_type}")

        return connection_strings[self.config.database_type.value]()

    def _get_sqlite_connection_string(self) -> str:
        """Generate SQLite connection string."""
        return f"sqlite:///{self.config.database}"

    def _get_postgresql_connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        if not all([self.config.host, self.config.username, self.config.database]):
            raise ValueError("PostgreSQL requires host, username, and database")

        port = self.config.port or 5432
        password_part = f":{self.config.password}" if self.config.password else ""
        return f"postgresql://{self.config.username}{password_part}@{self.config.host}:{port}/{self.config.database}"

    def _get_mysql_connection_string(self) -> str:
        """Generate MySQL connection string."""
        if not all([self.config.host, self.config.username, self.config.database]):
            raise ValueError("MySQL requires host, username, and database")

        port = self.config.port or 3306
        password_part = f":{self.config.password}" if self.config.password else ""
        return f"mysql+pymysql://{self.config.username}{password_part}@{self.config.host}:{port}/{self.config.database}"

    def _get_oracle_connection_string(self) -> str:
        """Generate Oracle connection string."""
        if not all([self.config.host, self.config.username, self.config.database]):
            raise ValueError("Oracle requires host, username, and database")

        port = self.config.port or 1521
        password_part = f":{self.config.password}" if self.config.password else ""
        dsn = f"{self.config.host}:{port}/{self.config.database}"
        return f"oracle+oracledb://{self.config.username}{password_part}@{dsn}"

    def _get_mssql_connection_string(self) -> str:
        """Generate Microsoft SQL Server connection string."""
        if not all([self.config.host, self.config.username, self.config.database]):
            raise ValueError("MSSQL requires host, username, and database")

        port = self.config.port or 1433
        password_part = f":{self.config.password}" if self.config.password else ""
        return f"mssql+pyodbc://{self.config.username}{password_part}@{self.config.host}:{port}/{self.config.database}?driver=ODBC+Driver+17+for+SQL+Server"

    def _connect_impl(self):
        """
        Establish connection to the specified database.

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            # Get connection string
            connect_args = {}
            self._encode_credentials()
            connection_string = self._get_connection_string()
            self._engine = create_engine(
                connection_string,
                echo=self.config.options["echo"],
                connect_args=self.config.options,
            )
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            # Create session factory
            self._session_factory = sessionmaker(bind=self._engine)
            self._session = self._session_factory()
            return self._session
        except (SQLAlchemyError, ValueError) as e:
            error = DatabaseConnectionError(
                message=f"Failed to connect to database: {e}",
                connection_params=self.get_info(),
            )
            raise error

    def _execute_impl(self, *args, **kwargs) -> List[OrderedDict[str, Any]]:
        """
        Execute a query and return results as a list of ordered dictionaries.

        Parameters:
            sql (str): The SQL query to execute.
            params (dict, optional): Optional parameters to pass to the query.

        Returns:
            List[OrderedDict]: A list of rows as ordered dictionaries with column names as keys.

        Raises:
            DatabaseQueryError: If the query execution fails.
        """
        try:
            # Log the query
            sql = args[0]
            params = kwargs.get("params")
            if self._session is None:
                self.connect()
            self._logger.info(f"Executing query: {sql}")
            if params:
                self._logger.info(f"With parameters: {params}")

            # Execute query
            result = self._session.execute(text(sql), params)

            # Check if the result returns rows
            if result.returns_rows:
                # Convert the result to a list of OrderedDicts
                rows_as_ordered_dicts = [
                    dict(zip(result.keys(), row)) for row in result.fetchall()
                ]
                # Log success
                self._logger.info(
                    f"Query executed successfully, {len(rows_as_ordered_dicts)} rows returned."
                )
                return rows_as_ordered_dicts
            else:
                # Log success for commands that do not return rows
                self._logger.info("Query executed successfully, no rows returned.")
                return []
        except Exception as e:
            raise DatabaseQueryError(
                message=str(e), query=args[0], params=kwargs.get("params")
            )

    def _disconnect_impl(self):
        """Close database connection."""
        if self._engine:
            self._session.close()
            self._engine.dispose()
            self._logger.info("Database connection closed.")

        # Reset state
        self._connection = None
        self._session_factory = None

    def __del__(self):
        """Ensure connection is closed when object is deleted."""
        self.disconnect()
