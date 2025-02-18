from pangolin_sdk.connections.ssh import SSHConnection, SSHConnectionConfig
from pangolin_sdk.constants import SSHAuthMethod


def test_ssh_connection():
    config = SSHConnectionConfig(
        name="test_ssh_connection",
        host="192.168.4.234",
        port=22,
        username="jarvis",
        password="M@nish123",
        auth_method=SSHAuthMethod.PASSWORD,
    )
    connection = SSHConnection(config)
    connection.execute("ls -l")
    result = connection.get_last_result()
    print(result)
