# -*- coding: utf-8 -*-
from setuptools import setup

packages = [
    "pangolin_sdk",
    "pangolin_sdk.configs",
    "pangolin_sdk.connections",
    "pangolin_sdk.utils",
    "pangolin_sdk.validations",
]

package_data = {"": ["*"]}

install_requires = [
    "cx-oracle>=8.3.0,<9.0.0",
    "kubernetes>=32.0.0,<33.0.0",
    "mysql-connector-python>=9.2.0,<10.0.0",
    "paramiko>=3.5.1,<4.0.0",
    "psycopg2-binary>=2.9.10,<3.0.0",
    "pyjwt>=2.10.1,<3.0.0",
    "requests>=2.32.3,<3.0.0",
    "sqlalchemy>=2.0.38,<3.0.0",
]

extras_require = {
    "dev": [
        "black>=25.1.0,<26.0.0",
        "pytest>=8.3.4,<9.0.0",
        "coverage>=7.6.12,<8.0.0",
        "pylint>=3.3.4,<4.0.0",
        "poetry2setup>=1.1.0,<2.0.0",
    ]
}

setup_kwargs = {
    "name": "pangolin-sdk",
    "version": "1.1.1",
    "description": "Developing a unified validation and verification system for IQ that automates testing across databases, SSH, APIs, Kubernetes, AWS, and Azure",
    "long_description": '# Pangolin SDK\n\nA unified validation and verification system that automates testing across databases, SSH, APIs, Kubernetes, AWS, and Azure.\n\n## Installation\n\n```bash\npip install pangolin-sdk\n```\n\n## Quick Start\n\n```python\nfrom pangolin_sdk.configs.database import DatabaseConnectionConfig\nfrom pangolin_sdk.connections.database import DatabaseConnection\nfrom pangolin_sdk.constants import DatabaseType\n\n# Create a configuration\nconfig = DatabaseConnectionConfig(\n    name="my-db",\n    host="localhost",\n    database_type=DatabaseType.POSTGRESQL,\n    database="mydb",\n    username="user",\n    password="pass"\n)\n\n# Use the connection\ndb = DatabaseConnection(config)\ntry:\n    db.execute("SELECT * FROM users")\n    results = db.get_last_result()\nfinally:\n    db.disconnect()\n```\n\n## Features\n\n- Unified interface for multiple connection types\n- Built-in connection lifecycle management\n- Comprehensive error handling\n- Support for:\n  - Databases (PostgreSQL, MySQL, Oracle, MSSQL, SQLite)\n  - APIs (REST with various auth methods)\n  - SSH connections\n  - Kubernetes clusters\n  - Cloud platforms (AWS, Azure)\n\n## Connection Documentation\n\n### Connection Lifecycle\n\nAll connections in Pangolin SDK follow a standard lifecycle:\n\n1. `connect()`: Establishes the connection\n2. `execute()`: Runs operations (handles connection automatically)\n3. `disconnect()`: Cleans up resources\n\n### Supported Connections\n\n#### Database Connections\n\n```python\nfrom pangolin_sdk.configs.database import DatabaseConnectionConfig\nfrom pangolin_sdk.constants import DatabaseType\n\nconfig = DatabaseConnectionConfig(\n    name="my-db",\n    host="localhost",\n    database_type=DatabaseType.POSTGRESQL,\n    port=5432,\n    database="mydb",\n    username="user",\n    password="pass"\n)\n\ndb = DatabaseConnection(config)\ntry:\n    db.execute("SELECT * FROM users WHERE age > :age", params={"age": 25})\n    results = db.get_last_result()\nfinally:\n    db.disconnect()\n```\n\n#### API Connections\n\n```python\nfrom pangolin_sdk.configs.api import APIConfig\nfrom pangolin_sdk.constants import AuthMethod\n\nconfig = APIConfig(\n    name="my-api",\n    host="https://api.example.com",\n    auth_method=AuthMethod.BEARER,\n    auth_token="your-token"\n)\n\napi = APIConnection(config)\ntry:\n    api.execute(\n        method="POST",\n        endpoint="/users",\n        data={"name": "John Doe"}\n    )\n    response = api.get_last_result()\nfinally:\n    api.disconnect()\n```\n\n#### SSH Connections\n\n```python\nfrom pangolin_sdk.configs.ssh import SSHConnectionConfig\nfrom pangolin_sdk.constants import SSHAuthMethod\n\nconfig = SSHConnectionConfig(\n    name="my-ssh",\n    host="ssh.example.com",\n    username="user",\n    auth_method=SSHAuthMethod.PASSWORD,\n    password="pass"\n)\n\nssh = SSHConnection(config)\ntry:\n    ssh.execute("ls -la")\n    output = ssh.get_last_result()\nfinally:\n    ssh.disconnect()\n```\n\n#### Kubernetes Connections\n\n```python\nfrom pangolin_sdk.configs.kubernetes import KubernetesConnectionConfig\nfrom pangolin_sdk.constants import KubernetesAuthMethod\n\nconfig = KubernetesConnectionConfig(\n    name="my-cluster",\n    auth_method=KubernetesAuthMethod.CONFIG,\n    kubeconfig_path="~/.kube/config",\n    namespace="default"\n)\n\nk8s = KubernetesConnection(config)\ntry:\n    k8s.execute(\n        resource_type=KubernetesResourceType.POD,\n        action="list",\n        namespace="default"\n    )\n    pods = k8s.get_last_result()\nfinally:\n    k8s.disconnect()\n```\n\n### Error Handling\n\n```python\ntry:\n    connection.execute(...)\n    result = connection.get_last_result()\nexcept ConnectionError as e:\n    print(f"Connection failed: {e.message}")\n    print(f"Details: {e.details}")\nexcept ExecutionError as e:\n    print(f"Execution failed: {e.message}")\nfinally:\n    connection.disconnect()\n```\n\n## AWS Connections\n\n### Configuration\n\nAWS connections support multiple authentication methods and service configurations through the `AWSConnectionConfig` class:\n\n```python\nfrom pangolin_sdk.configs.aws import AWSConnectionConfig\nfrom pangolin_sdk.constants import AWSAuthMethod, AWSService\n\nconfig = AWSConnectionConfig(\n    name="my-aws",\n    auth_method=AWSAuthMethod.CREDENTIALS,\n    region="us-west-2",\n    service=AWSService.S3,\n    \n    # For CREDENTIALS auth method\n    aws_access_key_id="your-access-key",\n    aws_secret_access_key="your-secret-key",\n    \n    # For PROFILE auth method\n    profile_name="default",\n    \n    # For ROLE auth method\n    role_arn="arn:aws:iam::account:role/role-name",\n    \n    # Optional configurations\n    session_token=None,  # For temporary credentials\n    endpoint_url=None,   # For custom endpoints\n    verify_ssl=True,\n    timeout=30\n)\n```\n\nSupported authentication methods:\n- Access Key Credentials (`AWSAuthMethod.CREDENTIALS`)\n- Profile Configuration (`AWSAuthMethod.PROFILE`)\n- IAM Role (`AWSAuthMethod.ROLE`)\n- Environment Variables (`AWSAuthMethod.ENVIRONMENT`)\n- EC2 Instance Profile (`AWSAuthMethod.INSTANCE_PROFILE`)\n\nSupported AWS services through `AWSService` enum:\n- S3 (`S3`)\n- EC2 (`EC2`)\n- RDS (`RDS`)\n- DynamoDB (`DYNAMODB`)\n- Lambda (`LAMBDA`)\n- SQS (`SQS`)\n- SNS (`SNS`)\n- CloudWatch (`CLOUDWATCH`)\n- IAM (`IAM`)\n- SES (`SES`)\n\n### Usage Example\n\n```python\nfrom pangolin_sdk.connections.aws import AWSConnection\nfrom pangolin_sdk.constants import AWSService\n\n# Create connection\naws = AWSConnection(config)\n\n# S3 operations\naws.execute(\n    service=AWSService.S3,\n    action="list_objects",\n    params={\n        "Bucket": "my-bucket",\n        "Prefix": "folder/"\n    }\n)\n\n# Get operation results\nobjects = aws.get_last_result()\nall_results = aws.get_results()\n\n# EC2 operations\naws.execute(\n    service=AWSService.EC2,\n    action="describe_instances",\n    params={\n        "Filters": [\n            {\n                "Name": "instance-state-name",\n                "Values": ["running"]\n            }\n        ]\n    }\n)\n\n# Clean up\naws.disconnect()\n```\n\n### Common Operations by Service\n\n#### S3 Operations\n```python\n# Upload file\naws.execute(\n    service=AWSService.S3,\n    action="upload_file",\n    params={\n        "Filename": "local_file.txt",\n        "Bucket": "my-bucket",\n        "Key": "remote_file.txt"\n    }\n)\n\n# Download file\naws.execute(\n    service=AWSService.S3,\n    action="download_file",\n    params={\n        "Bucket": "my-bucket",\n        "Key": "remote_file.txt",\n        "Filename": "downloaded_file.txt"\n    }\n)\n```\n\n#### EC2 Operations\n```python\n# Launch instance\naws.execute(\n    service=AWSService.EC2,\n    action="run_instances",\n    params={\n        "ImageId": "ami-12345678",\n        "InstanceType": "t2.micro",\n        "MinCount": 1,\n        "MaxCount": 1\n    }\n)\n\n# Stop instance\naws.execute(\n    service=AWSService.EC2,\n    action="stop_instances",\n    params={\n        "InstanceIds": ["i-1234567890abcdef0"]\n    }\n)\n```\n\n#### DynamoDB Operations\n```python\n# Put item\naws.execute(\n    service=AWSService.DYNAMODB,\n    action="put_item",\n    params={\n        "TableName": "my-table",\n        "Item": {\n            "id": {"S": "123"},\n            "name": {"S": "Test Item"}\n        }\n    }\n)\n\n# Query items\naws.execute(\n    service=AWSService.DYNAMODB,\n    action="query",\n    params={\n        "TableName": "my-table",\n        "KeyConditionExpression": "id = :id",\n        "ExpressionAttributeValues": {\n            ":id": {"S": "123"}\n        }\n    }\n)\n```\n\n### Error Handling\n\nAWS connections raise specific exceptions for AWS-related errors:\n\n```python\nfrom pangolin_sdk.exceptions import AWSConnectionError, AWSExecutionError\n\ntry:\n    aws.execute(\n        service=AWSService.S3,\n        action="list_objects",\n        params={"Bucket": "my-bucket"}\n    )\nexcept AWSConnectionError as e:\n    print(f"AWS Connection Error: {e.message}")\n    print(f"Service: {e.service}")\n    print(f"Region: {e.region}")\nexcept AWSExecutionError as e:\n    print(f"AWS Execution Error: {e.message}")\n    print(f"Service: {e.service}")\n    print(f"Action: {e.action}")\n    print(f"Error Code: {e.error_code}")\nfinally:\n    aws.disconnect()\n```\n\n## Best Practices\n\n1. Always use try/finally blocks to ensure proper cleanup\n2. Let execute() handle connections automatically\n3. Check connection status before critical operations\n4. Use error handling for robust applications\n5. Use appropriate authentication methods for each connection type\n\n## Detailed Documentation\n\nFor more detailed documentation about specific connection types and advanced usage:\n\n- [Connections Guide](docs/connections.md)\n- [API Reference](docs/api.md)\n- [Configuration Guide](docs/configuration.md)\n\n## License\n\nThis project is licensed under the AGPL-3.0 License - see the [LICENSE](LICENSE) file for details.\n\n## Contributing\n\nContributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.',
    "author": "Manish Kumar Bobbili",
    "author_email": "manishkumar.bobbili3@gmail.com",
    "maintainer": "None",
    "maintainer_email": "None",
    "url": "https://github.com/manish59/Pangolin/",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "extras_require": extras_require,
    "python_requires": ">=3.11,<4.0",
}


setup(**setup_kwargs)
