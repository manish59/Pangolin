from pangolin_sdk.connections.database import DatabaseConnection
from pangolin_sdk.configs.database import DatabaseConnectionConfig
from pangolin_sdk.constants import DatabaseType


def test_postgres_connection():
    host = "192.168.4.237"
    username = "manishbobbili"
    password = "M@nish123"
    database_name = "testing"
    config1 = DatabaseConnectionConfig(
        name="postgres-service-name",
        database_type=DatabaseType.POSTGRESQL,
        host=host,
        port=5432,
        service_name=database_name,
        username=username,
        password=password,
        database=database_name,
        options={"echo": False},
    )
    db = DatabaseConnection(config1)
    db.execute("SELECT * FROM test")
    results = db.get_last_result()
    print(results)


if __name__ == "__main__":
    test_postgres_connection()
# config1 = DatabaseConnectionConfig(
#     name="postgres-service-name",
#     database_type=DatabaseType.MYSQL,
#     host=host,
#     port=3306,
#     service_name=database_name,
#     username=username,
#     password=password,
#     database=database_name,
#     options={"echo": False},
# )
# db = DatabaseConnection(config1)
# results = db.query("SELECT * FROM test")
# print(results)
