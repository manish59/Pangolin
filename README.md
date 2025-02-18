# Pangolin SDK

A unified validation and verification system that automates testing across databases, SSH, APIs, Kubernetes, AWS, and Azure.

## Installation

```bash
pip install pangolin-sdk
```

## Quick Start

```python
from pangolin_sdk.configs.database import DatabaseConnectionConfig
from pangolin_sdk.connections.database import DatabaseConnection
from pangolin_sdk.constants import DatabaseType

# Create a configuration
config = DatabaseConnectionConfig(
    name="my-db",
    host="localhost",
    database_type=DatabaseType.POSTGRESQL,
    database="mydb",
    username="user",
    password="pass"
)

# Use the connection
db = DatabaseConnection(config)
try:
    db.execute("SELECT * FROM users")
    results = db.get_last_result()
finally:
    db.disconnect()
```

## Features

- Unified interface for multiple connection types
- Built-in connection lifecycle management
- Comprehensive error handling
- Support for:
  - Databases (PostgreSQL, MySQL, Oracle, MSSQL, SQLite)
  - APIs (REST with various auth methods)
  - SSH connections
  - Kubernetes clusters
  - Cloud platforms (AWS, Azure)

## Connection Documentation

### Connection Lifecycle

All connections in Pangolin SDK follow a standard lifecycle:

1. `connect()`: Establishes the connection
2. `execute()`: Runs operations (handles connection automatically)
3. `disconnect()`: Cleans up resources

### Supported Connections

#### Database Connections

```python
from pangolin_sdk.configs.database import DatabaseConnectionConfig
from pangolin_sdk.constants import DatabaseType

config = DatabaseConnectionConfig(
    name="my-db",
    host="localhost",
    database_type=DatabaseType.POSTGRESQL,
    port=5432,
    database="mydb",
    username="user",
    password="pass"
)

db = DatabaseConnection(config)
try:
    db.execute("SELECT * FROM users WHERE age > :age", params={"age": 25})
    results = db.get_last_result()
finally:
    db.disconnect()
```

#### API Connections

```python
from pangolin_sdk.configs.api import APIConfig
from pangolin_sdk.constants import AuthMethod

config = APIConfig(
    name="my-api",
    host="https://api.example.com",
    auth_method=AuthMethod.BEARER,
    auth_token="your-token"
)

api = APIConnection(config)
try:
    api.execute(
        method="POST",
        endpoint="/users",
        data={"name": "John Doe"}
    )
    response = api.get_last_result()
finally:
    api.disconnect()
```

#### SSH Connections

```python
from pangolin_sdk.configs.ssh import SSHConnectionConfig
from pangolin_sdk.constants import SSHAuthMethod

config = SSHConnectionConfig(
    name="my-ssh",
    host="ssh.example.com",
    username="user",
    auth_method=SSHAuthMethod.PASSWORD,
    password="pass"
)

ssh = SSHConnection(config)
try:
    ssh.execute("ls -la")
    output = ssh.get_last_result()
finally:
    ssh.disconnect()
```

#### Kubernetes Connections

```python
from pangolin_sdk.configs.kubernetes import KubernetesConnectionConfig
from pangolin_sdk.constants import KubernetesAuthMethod

config = KubernetesConnectionConfig(
    name="my-cluster",
    auth_method=KubernetesAuthMethod.CONFIG,
    kubeconfig_path="~/.kube/config",
    namespace="default"
)

k8s = KubernetesConnection(config)
try:
    k8s.execute(
        resource_type=KubernetesResourceType.POD,
        action="list",
        namespace="default"
    )
    pods = k8s.get_last_result()
finally:
    k8s.disconnect()
```

### Error Handling

```python
try:
    connection.execute(...)
    result = connection.get_last_result()
except ConnectionError as e:
    print(f"Connection failed: {e.message}")
    print(f"Details: {e.details}")
except ExecutionError as e:
    print(f"Execution failed: {e.message}")
finally:
    connection.disconnect()
```

## AWS Connections

### Configuration

AWS connections support multiple authentication methods and service configurations through the `AWSConnectionConfig` class:

```python
from pangolin_sdk.configs.aws import AWSConnectionConfig
from pangolin_sdk.constants import AWSAuthMethod, AWSService

config = AWSConnectionConfig(
    name="my-aws",
    auth_method=AWSAuthMethod.CREDENTIALS,
    region="us-west-2",
    service=AWSService.S3,
    
    # For CREDENTIALS auth method
    aws_access_key_id="your-access-key",
    aws_secret_access_key="your-secret-key",
    
    # For PROFILE auth method
    profile_name="default",
    
    # For ROLE auth method
    role_arn="arn:aws:iam::account:role/role-name",
    
    # Optional configurations
    session_token=None,  # For temporary credentials
    endpoint_url=None,   # For custom endpoints
    verify_ssl=True,
    timeout=30
)
```

Supported authentication methods:
- Access Key Credentials (`AWSAuthMethod.CREDENTIALS`)
- Profile Configuration (`AWSAuthMethod.PROFILE`)
- IAM Role (`AWSAuthMethod.ROLE`)
- Environment Variables (`AWSAuthMethod.ENVIRONMENT`)
- EC2 Instance Profile (`AWSAuthMethod.INSTANCE_PROFILE`)

Supported AWS services through `AWSService` enum:
- S3 (`S3`)
- EC2 (`EC2`)
- RDS (`RDS`)
- DynamoDB (`DYNAMODB`)
- Lambda (`LAMBDA`)
- SQS (`SQS`)
- SNS (`SNS`)
- CloudWatch (`CLOUDWATCH`)
- IAM (`IAM`)
- SES (`SES`)

### Usage Example

```python
from pangolin_sdk.connections.aws import AWSConnection
from pangolin_sdk.constants import AWSService

# Create connection
aws = AWSConnection(config)

# S3 operations
aws.execute(
    service=AWSService.S3,
    action="list_objects",
    params={
        "Bucket": "my-bucket",
        "Prefix": "folder/"
    }
)

# Get operation results
objects = aws.get_last_result()
all_results = aws.get_results()

# EC2 operations
aws.execute(
    service=AWSService.EC2,
    action="describe_instances",
    params={
        "Filters": [
            {
                "Name": "instance-state-name",
                "Values": ["running"]
            }
        ]
    }
)

# Clean up
aws.disconnect()
```

### Common Operations by Service

#### S3 Operations
```python
# Upload file
aws.execute(
    service=AWSService.S3,
    action="upload_file",
    params={
        "Filename": "local_file.txt",
        "Bucket": "my-bucket",
        "Key": "remote_file.txt"
    }
)

# Download file
aws.execute(
    service=AWSService.S3,
    action="download_file",
    params={
        "Bucket": "my-bucket",
        "Key": "remote_file.txt",
        "Filename": "downloaded_file.txt"
    }
)
```

#### EC2 Operations
```python
# Launch instance
aws.execute(
    service=AWSService.EC2,
    action="run_instances",
    params={
        "ImageId": "ami-12345678",
        "InstanceType": "t2.micro",
        "MinCount": 1,
        "MaxCount": 1
    }
)

# Stop instance
aws.execute(
    service=AWSService.EC2,
    action="stop_instances",
    params={
        "InstanceIds": ["i-1234567890abcdef0"]
    }
)
```

#### DynamoDB Operations
```python
# Put item
aws.execute(
    service=AWSService.DYNAMODB,
    action="put_item",
    params={
        "TableName": "my-table",
        "Item": {
            "id": {"S": "123"},
            "name": {"S": "Test Item"}
        }
    }
)

# Query items
aws.execute(
    service=AWSService.DYNAMODB,
    action="query",
    params={
        "TableName": "my-table",
        "KeyConditionExpression": "id = :id",
        "ExpressionAttributeValues": {
            ":id": {"S": "123"}
        }
    }
)
```

### Error Handling

AWS connections raise specific exceptions for AWS-related errors:

```python
from pangolin_sdk.exceptions import AWSConnectionError, AWSExecutionError

try:
    aws.execute(
        service=AWSService.S3,
        action="list_objects",
        params={"Bucket": "my-bucket"}
    )
except AWSConnectionError as e:
    print(f"AWS Connection Error: {e.message}")
    print(f"Service: {e.service}")
    print(f"Region: {e.region}")
except AWSExecutionError as e:
    print(f"AWS Execution Error: {e.message}")
    print(f"Service: {e.service}")
    print(f"Action: {e.action}")
    print(f"Error Code: {e.error_code}")
finally:
    aws.disconnect()
```

## Best Practices

1. Always use try/finally blocks to ensure proper cleanup
2. Let execute() handle connections automatically
3. Check connection status before critical operations
4. Use error handling for robust applications
5. Use appropriate authentication methods for each connection type

## Detailed Documentation

For more detailed documentation about specific connection types and advanced usage:

- [Connections Guide](docs/connections.md)
- [API Reference](docs/api.md)
- [Configuration Guide](docs/configuration.md)

## License

This project is licensed under the AGPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.