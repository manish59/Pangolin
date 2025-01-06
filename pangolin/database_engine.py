import logging
from typing import Any, List, Dict, Optional, Union

import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from pangolin.exceptions import DatabaseConnectionError, DatabaseQueryError
from pangolin.engine import Engine

class Database_Engine(Engine):
    """
    Unified Database Engine supporting multiple database types.

    Supports:
    - SQLite
    - PostgreSQL
    - MySQL
    - Oracle
    - Microsoft SQL Server
    """

    def __init__(
            self,
            database_type: str,
            database: str,
            host: Optional[str] = None,
            port: Optional[int] = None,
            username: Optional[str] = None,
            password: Optional[str] = None,
            **config
    ):
        """
        Initialize database engine with connection parameters.

        Args:
            database_type (str): Type of database
            database (str): Database name or path
            host (Optional[str], optional): Database host
            port (Optional[int], optional): Database port
            username (Optional[str], optional): Database username
            password (Optional[str], optional): Database password
            **config: Additional configuration options
        """
        # Default configuration
        self.config = {
            "timeout": 10,
            "logging_enabled": True,
            "connection_retries": 3,
            "echo": False
        }
        self.config.update(config)

        # Logging setup
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.logger.setLevel(
            logging.DEBUG if self.config["logging_enabled"] else logging.ERROR
        )

        # Connection parameters
        self.database_type = database_type.lower()
        self.database = database
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        # SQLAlchemy components
        self._engine = None
        self._session_factory = None

        # Query state
        self._last_query_result = None
        self._last_error = None

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
            'sqlite': self._get_sqlite_connection_string,
            'postgresql': self._get_postgresql_connection_string,
            'mysql': self._get_mysql_connection_string,
            'oracle': self._get_oracle_connection_string,
            'mssql': self._get_mssql_connection_string
        }

        # Get and validate connection string generator
        if self.database_type not in connection_strings:
            raise ValueError(f"Unsupported database type: {self.database_type}")

        return connection_strings[self.database_type]()

    def _get_sqlite_connection_string(self) -> str:
        """Generate SQLite connection string."""
        return f'sqlite:///{self.database}'

    def _get_postgresql_connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        if not all([self.host, self.username, self.database]):
            raise ValueError("PostgreSQL requires host, username, and database")

        port = self.port or 5432
        password_part = f":{self.password}" if self.password else ""
        return f'postgresql://{self.username}{password_part}@{self.host}:{port}/{self.database}'

    def _get_mysql_connection_string(self) -> str:
        """Generate MySQL connection string."""
        if not all([self.host, self.username, self.database]):
            raise ValueError("MySQL requires host, username, and database")

        port = self.port or 3306
        password_part = f":{self.password}" if self.password else ""
        return f'mysql+pymysql://{self.username}{password_part}@{self.host}:{port}/{self.database}'

    def _get_oracle_connection_string(self) -> str:
        """Generate Oracle connection string."""
        if not all([self.host, self.username, self.database]):
            raise ValueError("Oracle requires host, username, and database")

        port = self.port or 1521
        password_part = f":{self.password}" if self.password else ""
        dsn = f'{self.host}:{port}/{self.database}'
        return f'oracle+cx_oracle://{self.username}{password_part}@{dsn}'

    def _get_mssql_connection_string(self) -> str:
        """Generate Microsoft SQL Server connection string."""
        if not all([self.host, self.username, self.database]):
            raise ValueError("MSSQL requires host, username, and database")

        port = self.port or 1433
        password_part = f":{self.password}" if self.password else ""
        return f'mssql+pyodbc://{self.username}{password_part}@{self.host}:{port}/{self.database}?driver=ODBC+Driver+17+for+SQL+Server'

    def setup(self):
        """
        Establish connection to the specified database.

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            # Get connection string
            connection_string = self._get_connection_string()

            # Create SQLAlchemy engine
            self._engine = create_engine(
                connection_string,
                echo=self.config['echo'],
                connect_args={
                    'connect_timeout': self.config['timeout']
                }
            )

            # Test connection
            with self._engine.connect() as connection:
                connection.execute(text('SELECT 1'))

            # Create session factory
            self._session_factory = sessionmaker(bind=self._engine)

            self.logger.info(f"Connected to {self.database_type} database successfully")

        except (SQLAlchemyError, ValueError) as e:
            self.logger.error(f"Database connection error: {e}")
            self._last_error = str(e)
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")

    def execute(
            self,
            query: str,
            params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a database query.

        Args:
            query (str): SQL query to execute
            params (Optional[Dict[str, Any]]): Query parameters

        Returns:
            List[Dict[str, Any]]: Query results

        Raises:
            DatabaseQueryError: If query execution fails
        """
        if not self._engine:
            raise DatabaseConnectionError("Not connected. Call setup() first.")

        try:
            # Create a new session
            session = self._session_factory()

            self.logger.info(f"Executing query: {query}")

            # Prepare query
            sql_query = text(query)

            # Execute query
            result = session.execute(sql_query, params or {})

            # Convert results to list of dictionaries
            if result.keys():
                results = [dict(row) for row in result]
                self._last_query_result = results
                self.logger.debug(f"Query returned {len(results)} rows")

                # Close session
                session.close()

                return results

            # Commit for non-SELECT queries
            session.commit()

            # Close session
            session.close()

            return []

        except SQLAlchemyError as e:
            self.logger.error(f"Query execution error: {e}")
            self._last_error = str(e)
            raise DatabaseQueryError(f"Failed to execute query: {e}")

    def result(self):
        """
        Return the result of the last executed query.

        Returns:
            List[Dict[str, Any]]: Results of the last query
        """
        return self._last_query_result or []

    def error(self):
        """
        Return the error of the last operation.

        Returns:
            str: Error message of the last operation
        """
        return self._last_error or ""

    def disconnect(self):
        """Close database connection."""
        if self._engine:
            self._engine.dispose()
            self.logger.info("Database connection closed.")

        # Reset state
        self._engine = None
        self._session_factory = None

    def __del__(self):
        """Ensure connection is closed when object is deleted."""
        self.disconnect()


# Example usage
def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Example database connections
    database_configs = [
        # SQLite Example
        {
            'database_type': 'sqlite',
            'database': 'example.db'
        },
        # PostgreSQL Example (commented out)
        # {
        #     'database_type': 'postgresql',
        #     'host': 'localhost',
        #     'database': 'mydb',
        #     'username': 'myuser',
        #     'password': 'mypassword'
        # },
        # Oracle Example (commented out)
        # {
        #     'database_type': 'oracle',
        #     'host': 'localhost',
        #     'database': 'mydb',
        #     'username': 'myuser',
        #     'password': 'mypassword'
        # },
        # MSSQL Example (commented out)
        # {
        #     'database_type': 'mssql',
        #     'host': 'localhost',
        #     'database': 'mydb',
        #     'username': 'myuser',
        #     'password': 'mypassword'
        # }
    ]

    # Iterate through database configurations
    for db_config in database_configs:
        try:
            # Create database engine
            engine = Engine(**db_config)

            # Establish connection
            engine.setup()

            # Execute a sample query
            if db_config['database_type'] == 'sqlite':
                # Create table for SQLite
                engine.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        email TEXT
                    )
                ''')

                # Insert sample data
                engine.execute(
                    'INSERT INTO users (name, email) VALUES (:name, :email)',
                    {'name': 'John Doe', 'email': 'john@example.com'}
                )

            # Query data
            results = engine.execute('SELECT * FROM users')
            print(f"{db_config['database_type'].upper()} Results:", results)

            # Get last result
            print("Last Result:", engine.result())

        except (DatabaseConnectionError, DatabaseQueryError) as e:
            print(f"{db_config['database_type'].upper()} Error: {e}")


if __name__ == '__main__':
    main()