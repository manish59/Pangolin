from pangolin_sdk.connections.api import APIConnection
from pangolin_sdk.configs.api import APIConfig
from pangolin_sdk.constants import AuthMethod


def test_api_connection_get():
    config = APIConfig(
        name="test_api",
        host="https://jsonplaceholder.typicode.com/posts/1",
        auth_method=AuthMethod.NONE,
        default_headers={"Content-Type": "application/json"},
        timeout=5,
    )
    api_connection = APIConnection(config=config)
    api_connection.execute(method="GET", endpoint="/")
    data = {"id": 1, "title": "...", "body": "...", "userId": 1}
    result = api_connection.get_last_result()
    assert result["status_code"] == 200
    assert result["data"].keys() == data.keys()


def test_api_connection_post():
    data = {"title": "foo", "body": "bar", "userId": 1}
    config = APIConfig(
        name="test_api",
        host="https://jsonplaceholder.typicode.com/",
        auth_method=AuthMethod.NONE,
        default_headers={"Content-Type": "application/json"},
        timeout=5,
    )
    api_connection = APIConnection(config=config)
    api_connection.execute(method="POST", endpoint="/posts", data=data)
    result = api_connection.get_last_result()
    assert result["status_code"] == 201
    data["id"] = 101
    assert result["data"].keys() == data.keys()


def test_api_connection_put():
    data = {"title": "foo", "body": "bar", "userId": 1, "id": 1}
    config = APIConfig(
        name="test_api",
        host="https://jsonplaceholder.typicode.com/",
        auth_method=AuthMethod.NONE,
        default_headers={"Content-Type": "application/json"},
        timeout=5,
    )
    api_connection = APIConnection(config=config)
    api_connection.execute(method="PUT", endpoint="/posts/1", data=data)
    result = api_connection.get_last_result()
    assert result["status_code"] == 200
    assert result["data"].keys() == data.keys()


def test_api_connection_patch():
    data = {"title": "foo", "body": "bar", "userId": 1, "id": 1}
    config = APIConfig(
        name="test_api",
        host="https://jsonplaceholder.typicode.com/",
        auth_method=AuthMethod.NONE,
        default_headers={"Content-Type": "application/json"},
        timeout=5,
    )
    api_connection = APIConnection(config=config)
    api_connection.execute(method="PUT", endpoint="/posts/1", data=data)
    result = api_connection.get_last_result()
    assert result["status_code"] == 200
    assert result["data"].keys() == data.keys()


def test_api_connection_delete():
    data = {"title": "foo", "body": "bar", "userId": 1, "id": 1}
    config = APIConfig(
        name="test_api",
        host="https://jsonplaceholder.typicode.com/",
        auth_method=AuthMethod.NONE,
        default_headers={"Content-Type": "application/json"},
        timeout=5,
    )
    api_connection = APIConnection(config=config)
    api_connection.execute(method="DELETE", endpoint="/posts/1")
    result = api_connection.get_last_result()
    assert result["status_code"] == 200


def test_api_connection_get_with_params():
    config = APIConfig(
        name="test_api",
        host="https://jsonplaceholder.typicode.com/posts/1",
        auth_method=AuthMethod.NONE,
        default_headers={"Content-Type": "application/json"},
        timeout=5,
    )
    api_connection = APIConnection(config=config)
    api_connection.execute(method="GET", endpoint="/", params={"userId": 1})
    data = {"id": 1, "title": "...", "body": "...", "userId": 1}
    result = api_connection.get_last_result()
    print(result["data"])
    assert result["status_code"] == 200
    data["userId"] = 1
    assert result["data"].keys() == data.keys()


def test_basic_auth():
    config = APIConfig(
        name="test_api",
        host="https://httpbin.org",
        auth_method=AuthMethod.BASIC,
        username="user",
        password="pass",
        default_headers={"Content-Type": "application/json"},
        timeout=5,
    )
    api_connection = APIConnection(config=config)
    api_connection.execute(method="GET", endpoint="/basic-auth/user/pass")
    result = api_connection.get_last_result()
    assert result["status_code"] == 200
    assert result["data"]["authenticated"] is True
    assert result["data"]["user"] == "user"


def test_digest_auth():
    config = APIConfig(
        name="test_api",
        host="https://httpbin.org",
        auth_method=AuthMethod.DIGEST,
        username="user",
        password="pass",
        default_headers={"Content-Type": "application/json"},
        timeout=5,
    )
    api_connection = APIConnection(config=config)
    api_connection.execute(method="GET", endpoint="/digest-auth/auth/user/pass")
    result = api_connection.get_last_result()
    print(result)
    assert result["status_code"] == 200
    assert result["data"]["authenticated"] is True
    assert result["data"]["user"] == "user"


def test_bearer_token():
    config = APIConfig(
        name="test_api",
        host="https://httpbin.org",
        auth_method=AuthMethod.BEARER,
        auth_token="test_token",
        default_headers={"Content-Type": "application/json"},
        timeout=5,
    )
    api_connection = APIConnection(config=config)
    api_connection.execute(method="GET", endpoint="/bearer")
    result = api_connection.get_last_result()
    print(result)
    assert result["status_code"] == 200
    assert result["data"]["authenticated"] is True
    assert result["data"]["token"] == "test_token"


def test_api_key_in_header():
    config = APIConfig(
        name="test_api",
        host="https://httpbin.org",
        auth_method=AuthMethod.API_KEY,
        api_key_name="X-API-Key",
        api_key="your_api_key",
        api_key_location="header",
        default_headers={"Content-Type": "application/json"},
        timeout=5,
    )
    api_connection = APIConnection(config=config)
    api_connection.execute(method="GET", endpoint="/headers")
    result = api_connection.get_last_result()
    print(result)
    assert result["status_code"] == 200
    assert result["data"]["headers"]["X-Api-Key"] == "your_api_key"


def test_api_key_in_query():
    config = APIConfig(
        name="test_api",
        host="https://httpbin.org",
        auth_method=AuthMethod.API_KEY,
        api_key_name="api_key",
        api_key="your_api_key",
        api_key_location="query",
        default_headers={"Content-Type": "application/json"},
        timeout=5,
    )
    api_connection = APIConnection(config=config)
    api_connection.execute(
        method="GET", endpoint="/get", params={"api_key": "your_api_key"}
    )
    result = api_connection.get_last_result()
    assert result["status_code"] == 200
    assert result["data"]["args"]["api_key"] == "your_api_key"


if __name__ == "__main__":
    test_basic_auth()
    test_digest_auth()
    test_bearer_token()
    test_api_key_in_header()
    test_api_key_in_query()
