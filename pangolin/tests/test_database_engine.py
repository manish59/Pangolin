import unittest
from unittest.mock import Mock, patch
from sqlalchemy.exc import SQLAlchemyError
from pangolin.exceptions import DatabaseConnectionError, DatabaseQueryError
from pangolin.database_engine import Database_Engine


class TestDatabaseEngine(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.sqlite_config = {"database_type": "sqlite", "database": ":memory:"}

        self.postgres_config = {
            "database_type": "postgresql",
            "database": "test_db",
            "host": "localhost",
            "port": 5432,
            "username": "test_user",
            "password": "test_pass",
        }

    def test_init_with_minimal_config(self):
        """Test initialization with minimal configuration"""
        engine = Database_Engine(**self.sqlite_config)
        self.assertEqual(engine.database_type, "sqlite")
        self.assertEqual(engine.database, ":memory:")
        self.assertIsNone(engine.host)
        self.assertIsNone(engine.port)

    def test_init_with_full_config(self):
        """Test initialization with full configuration"""
        engine = Database_Engine(**self.postgres_config)
        self.assertEqual(engine.database_type, "postgresql")
        self.assertEqual(engine.host, "localhost")
        self.assertEqual(engine.port, 5432)
        self.assertEqual(engine.username, "test_user")
        self.assertEqual(engine.password, "test_pass")

    def test_get_sqlite_connection_string(self):
        """Test SQLite connection string generation"""
        engine = Database_Engine(**self.sqlite_config)
        connection_string = engine._get_sqlite_connection_string()
        self.assertEqual(connection_string, "sqlite:///:memory:")

    def test_get_postgresql_connection_string(self):
        """Test PostgreSQL connection string generation"""
        engine = Database_Engine(**self.postgres_config)
        connection_string = engine._get_postgresql_connection_string()
        self.assertEqual(
            connection_string, "postgresql://test_user:test_pass@localhost:5432/test_db"
        )

    def test_postgresql_connection_string_without_password(self):
        """Test PostgreSQL connection string generation without password"""
        config = self.postgres_config.copy()
        config["password"] = None
        engine = Database_Engine(**config)
        connection_string = engine._get_postgresql_connection_string()
        self.assertEqual(
            connection_string, "postgresql://test_user@localhost:5432/test_db"
        )

    def test_invalid_database_type(self):
        """Test handling of invalid database type"""
        with self.assertRaises(ValueError):
            engine = Database_Engine(database_type="invalid_db", database="test_db")
            engine._get_connection_string()

    @patch("sqlalchemy.create_engine")
    def test_setup_success(self, mock_create_engine):
        """Test successful database setup"""
        # Mock the engine and connection
        mock_engine = Mock()
        mock_connection = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        engine = Database_Engine(**self.sqlite_config)
        engine.setup()

        # Verify create_engine was called
        mock_create_engine.assert_called_once()
        self.assertIsNotNone(engine._connection)

    @patch("sqlalchemy.create_engine")
    def test_setup_failure(self, mock_create_engine):
        """Test database setup failure"""
        # Mock SQLAlchemy error
        mock_create_engine.side_effect = SQLAlchemyError("Connection failed")

        engine = Database_Engine(**self.sqlite_config)
        with self.assertRaises(DatabaseConnectionError):
            engine.setup()

    @patch("sqlalchemy.create_engine")
    def test_execute_query_success(self, mock_create_engine):
        """Test successful query execution"""
        # Mock the engine and session
        mock_engine = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_result.keys.return_value = ["id", "name"]
        mock_result.__iter__ = lambda _: iter([{"id": 1, "name": "test"}])

        mock_session.execute.return_value = mock_result
        mock_session_factory = Mock(return_value=mock_session)

        mock_create_engine.return_value = mock_engine

        # Setup and execute query
        engine = Database_Engine(**self.sqlite_config)
        engine._connection = mock_engine
        engine._session_factory = mock_session_factory

        result = engine.execute("SELECT * FROM test")

        # Verify results
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[0]["name"], "test")

        # Verify session handling
        mock_session.execute.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("sqlalchemy.create_engine")
    def test_execute_query_failure(self, mock_create_engine):
        """Test query execution failure"""
        # Mock the engine and session
        mock_engine = Mock()
        mock_session = Mock()
        mock_session.execute.side_effect = SQLAlchemyError("Query failed")
        mock_session_factory = Mock(return_value=mock_session)

        mock_create_engine.return_value = mock_engine

        # Setup and attempt query
        engine = Database_Engine(**self.sqlite_config)
        engine._connection = mock_engine
        engine._session_factory = mock_session_factory

        with self.assertRaises(DatabaseQueryError):
            engine.execute("SELECT * FROM test")

    def test_disconnect(self):
        """Test database disconnection"""
        engine = Database_Engine(**self.sqlite_config)
        mock_connection = Mock()
        engine._connection = mock_connection

        engine.disconnect()

        # Verify connection was disposed
        mock_connection.dispose.assert_called_once()
        self.assertIsNone(engine._connection)
        self.assertIsNone(engine._session_factory)

    def test_result_and_error_methods(self):
        """Test result() and error() methods"""
        engine = Database_Engine(**self.sqlite_config)

        # Test initial state
        self.assertEqual(engine.result(), [])
        self.assertEqual(engine.error(), "")

        # Test after setting values
        test_results = [{"id": 1, "name": "test"}]
        test_error = "Test error message"

        engine._last_query_result = test_results
        engine._last_error = test_error

        self.assertEqual(engine.result(), test_results)
        self.assertEqual(engine.error(), test_error)


if __name__ == "__main__":
    unittest.main()
