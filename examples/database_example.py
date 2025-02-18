from pangolin_sdk.configs.database import DatabaseConnectionConfig
from pangolin_sdk.constants import DatabaseType
from pangolin_sdk.connections.database import DatabaseConnection
from pangolin_sdk.exceptions import DatabaseConnectionError, DatabaseQueryError


def main():
    # Create database configuration
    config = DatabaseConnectionConfig(
        name="example-db",
        host="192.168.4.234",
        database_type=DatabaseType.POSTGRESQL,
        port=5432,
        database="testing",
        username="manishbobbili",
        password="M@nish123",
        # Optional settings
        timeout=30,
        max_retries=3,
        retry_interval=5,
        options={"echo": False, "tcp_connect_timeout": 10},  # SQL query logging
    )

    # Create database connection
    db = DatabaseConnection(config)

    try:
        # Create tables
        create_tables_query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            amount DECIMAL(10,2) NOT NULL,
            status VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        db.execute(create_tables_query)

        # Insert sample users
        insert_users_query = """
        INSERT INTO users (name, email) VALUES
            (:name, :email)
        RETURNING id, name, email;
        """
        users = db.execute(
            insert_users_query, params={"name": "John Doe", "email": "john@example.com"}
        )
        print("Inserted user:", db.get_last_result())

        # Insert sample orders
        insert_orders_query = """
        INSERT INTO orders (user_id, amount, status) VALUES
            (:user_id, :amount, :status)
        RETURNING id, user_id, amount, status;
        """
        user_id = db.get_last_result()[0]["id"]
        orders = db.execute(
            insert_orders_query,
            params={"user_id": user_id, "amount": 99.99, "status": "pending"},
        )
        print("Inserted order:", db.get_last_result())

        # Query with JOIN
        select_query = """
        SELECT 
            u.name,
            u.email,
            o.amount,
            o.status,
            o.created_at
        FROM users u
        JOIN orders o ON u.id = o.user_id
        WHERE o.amount > :min_amount
        ORDER BY o.created_at DESC;
        """
        results = db.execute(select_query, params={"min_amount": 50})
        print("Query results:", db.get_last_result())

        # Aggregation query
        stats_query = """
        SELECT 
            u.name,
            COUNT(o.id) as total_orders,
            SUM(o.amount) as total_spent,
            AVG(o.amount) as avg_order_amount
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        GROUP BY u.id, u.name
        HAVING COUNT(o.id) > 0;
        """
        stats = db.execute(stats_query)
        print("User statistics:", db.get_last_result())

    except DatabaseConnectionError as e:
        print(f"Connection error: {e.message}")
        print(f"Details: {e.details}")
        print(f"Timestamp: {e.timestamp}")

    except DatabaseQueryError as e:
        print(f"Query error: {e.message}")
        print(f"Query: {e.query}")
        print(f"Parameters: {e.params}")

    finally:
        # Always disconnect
        db.disconnect()


if __name__ == "__main__":
    main()
