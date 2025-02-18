# Pangolin SDK Configuration Guide

This guide provides detailed configuration information for all connection types in the Pangolin SDK.

## Common Configuration Parameters

All connection configurations inherit from `BaseConfig` and `ConnectionConfig`, which provide these common parameters:

```python
from pangolin_sdk.configs.base import ConnectionConfig

config = ConnectionConfig(
    # Required parameters
    name="my-connection",    # Unique identifier for the connection
    host="example.com",      # Host to connect to
    
    # Optional parameters
    username=None,           # Username for authentication
    password=None,          # Password for authentication
    timeout=30,             # Connection timeout in seconds
    max_retries=3,          # Maximum number of retry attempts
    retry_interval=5,       # Base interval between retries in seconds
    retry_backoff=1.5,      # Multiplier for retry interval
    retry_jitter=True,      # Add randomness to retry intervals
    ssl_enabled=True,       # Enable SSL/TLS
    ssl_verify=True,        # Verify SSL certificates
    options={}              # Additional connection-specific options
)
```

## Database Configurations

Database connections support multiple database types and connection methods:

```python
from pangolin_sdk.configs.database import DatabaseConnectionConfig
from pangolin_sdk.constants import DatabaseType

config = DatabaseConnectionConfig(
    # Common parameters
    name="my-db",
    host="localhost",
    username="user",
    password="pass",
    
    # Database-specific parameters
    database_type=DatabaseType.POSTGRESQL,  # Type of database
    port=5432,                             # Database port
    database="mydb",                       # Database name
    connection_string=None,                # Optional: full connection string
    schema=None,                           # Optional: database schema
    
    # Oracle-specific parameters
    service_name=None,                     # Oracle service name
    sid=None,                             # Oracle SID
    tns_name=None,                        # Oracle TNS name
)
```

Supported database types:
- `DatabaseType.POSTGRESQL` (port 5432)
- `DatabaseType.MYSQL` (port 3306)
- `DatabaseType.ORACLE` (port 1521)
- `DatabaseType.MSSQL` (port 1433)
- `DatabaseType.SQLITE` (no port required)

### Database-Specific Requirements

#### PostgreSQL
```python
config = DatabaseConnectionConfig(
    database_type=DatabaseType.POSTGRESQL,
    host="localhost",
    port=5432,
    database="mydb",
    username="user",
    password="pass"
)
```

#### MySQL
```python
config = DatabaseConnectionConfig(
    database_type=DatabaseType.MYSQL,
    host="localhost",
    port=3306,
    database="mydb",
    username="user",
    password="pass"
)
```

#### Oracle
```python
# Using service name
config = DatabaseConnectionConfig(
    database_type=DatabaseType.ORACLE,
    host="localhost",
    port=1521,
    service_name="myservice",
    username="user",
    password="pass"
)

# Using SID
config = DatabaseConnectionConfig(
    database_type=DatabaseType.ORACLE,
    host="localhost",
    port=1521,
    sid="mysid",
    username="user",
    password="pass"
)

# Using TNS name
config = DatabaseConnectionConfig(
    database_type=DatabaseType.ORACLE,
    tns_name="mytns",
    username="user",
    password="pass"
)
```

#### MSSQL
```python
config = DatabaseConnectionConfig(
    database_type=DatabaseType.MSSQL,
    host="localhost",
    port=1433,
    database="mydb",
    username="user",
    password="pass"
)
```

#### SQLite
```python
config = DatabaseConnectionConfig(
    database_type=DatabaseType.SQLITE,
    database="/path/to/database.db"  # File path for SQLite database
)
```

## API Configurations

API connections support various authentication methods and header configurations:

```python
from pangolin_sdk.configs.api import APIConfig
from pangolin_sdk.constants import AuthMethod

config = APIConfig(
    # Common parameters
    name="my-api",
    host="https://api.example.com",
    
    # Authentication
    auth_method=AuthMethod.BEARER,         # Authentication method
    auth_token=None,                       # For Bearer/JWT auth
    api_key=None,                          # For API key auth
    api_key_name=None,                     # Header/query param name for API key
    api_key_location="header",             # "header" or "query"
    
    # OAuth2 parameters
    oauth_client_id=None,
    oauth_client_secret=None,
    oauth_scope=None,
    
    # JWT specific
    jwt_secret=None,
    jwt_algorithm="HS256",
    
    # HMAC parameters
    hmac_key=None,
    hmac_secret=None,
    hmac_algorithm="sha256",
    
    # Headers
    default_headers={                      # Default headers for all requests
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
)
```

Supported authentication methods:
- `AuthMethod.NONE` - No authentication
- `AuthMethod.BASIC` - Basic auth with username/password
- `AuthMethod.BEARER` - Bearer token auth
- `AuthMethod.JWT` - JWT token auth
- `AuthMethod.API_KEY` - API key auth
- `AuthMethod.OAUTH2` - OAuth2 authentication
- `AuthMethod.HMAC` - HMAC authentication
- `AuthMethod.DIGEST` - Digest authentication

### Auth Method Examples

#### Basic Auth
```python
config = APIConfig(
    name="my-api",
    host="https://api.example.com",
    auth_method=AuthMethod.BASIC,
    username="user",
    password="pass"
)
```

#### Bearer Token
```python
config = APIConfig(
    name="my-api",
    host="https://api.example.com",
    auth_method=AuthMethod.BEARER,
    auth_token="your-bearer-token"
)
```

#### API Key
```python
config = APIConfig(
    name="my-api",
    host="https://api.example.com",
    auth_method=AuthMethod.API_KEY,
    api_key="your-api-key",
    api_key_name="X-API-Key",
    api_key_location="header"  # or "query"
)
```

#### OAuth2
```python
config = APIConfig(
    name="my-api",
    host="https://api.example.com",
    auth_method=AuthMethod.OAUTH2,
    oauth_client_id="client-id",
    oauth_client_secret="client-secret",
    oauth_scope="read write"
)
```

#### HMAC
```python
config = APIConfig(
    name="my-api",
    host="https://api.example.com",
    auth_method=AuthMethod.HMAC,
    hmac_key="your-key",
    hmac_secret="your-secret",
    hmac_algorithm="sha256"
)
```

## SSH Configurations

SSH connections support password, public key, and agent-based authentication:

```python
from pangolin_sdk.configs.ssh import SSHConnectionConfig
from pangolin_sdk.constants import SSHAuthMethod, ParamikoKey

config = SSHConnectionConfig(
    # Common parameters
    name="my-ssh",
    host="ssh.example.com",
    port=22,
    username="user",
    
    # Authentication method
    auth_method=SSHAuthMethod.PASSWORD,    # Authentication method
    
    # For password auth
    password="pass",                       # Required for PASSWORD auth
    
    # For public key auth
    key_filename=None,                     # Path to private key file
    pkey=None,                            # Paramiko key object
    pkey_type=ParamikoKey.RSA,            # Key type for public key auth
    passphrase=None,                      # Passphrase for encrypted keys
    
    # For SSH agent auth
    allow_agent=True,                      # Allow SSH agent
    look_for_keys=True,                    # Look for keys in ~/.ssh/
    
    # Advanced options
    banner_timeout=15,                     # Banner timeout in seconds
    sock=None,                            # Socket for proxy support
)
```

Supported authentication methods:
- `SSHAuthMethod.PASSWORD` - Password authentication
- `SSHAuthMethod.PUBLIC_KEY` - Public key authentication
- `SSHAuthMethod.AGENT` - SSH agent authentication

Supported key types:
- `ParamikoKey.RSA` - RSA keys
- `ParamikoKey.DSS` - DSS keys
- `ParamikoKey.ECDSA` - ECDSA keys
- `ParamikoKey.ED25519` - ED25519 keys

### Auth Method Examples

#### Password Authentication
```python
config = SSHConnectionConfig(
    name="my-ssh",
    host="ssh.example.com",
    username="user",
    auth_method=SSHAuthMethod.PASSWORD,
    password="pass"
)
```

#### Public Key Authentication
```python
config = SSHConnectionConfig(
    name="my-ssh",
    host="ssh.example.com",
    username="user",
    auth_method=SSHAuthMethod.PUBLIC_KEY,
    key_filename="~/.ssh/id_rsa",
    pkey_type=ParamikoKey.RSA,
    passphrase="optional-passphrase"
)
```

#### SSH Agent Authentication
```python
config = SSHConnectionConfig(
    name="my-ssh",
    host="ssh.example.com",
    username="user",
    auth_method=SSHAuthMethod.AGENT,
    allow_agent=True,
    look_for_keys=True
)
```

## AWS Configurations

AWS connections support multiple authentication methods and services:

```python
from pangolin_sdk.configs.aws import AWSConnectionConfig
from pangolin_sdk.constants import AWSAuthMethod, AWSService

config = AWSConnectionConfig(
    # Common parameters
    name="my-aws",
    region="us-west-2",
    
    # Authentication method
    auth_method=AWSAuthMethod.CREDENTIALS,
    
    # For credentials auth
    aws_access_key_id="your-access-key",
    aws_secret_access_key="your-secret-key",
    
    # For profile auth
    profile_name="default",
    
    # For role auth
    role_arn="arn:aws:iam::account:role/role-name",
    
    # Service configuration
    service=AWSService.S3,                 # AWS service to use
    endpoint_url=None,                     # Custom endpoint URL
    session_token=None,                    # For temporary credentials
    verify_ssl=True,                       # Verify SSL certificates
)
```

Supported authentication methods:
- `AWSAuthMethod.CREDENTIALS` - Access key credentials
- `AWSAuthMethod.PROFILE` - AWS profile
- `AWSAuthMethod.ROLE` - IAM role
- `AWSAuthMethod.ENVIRONMENT` - Environment variables
- `AWSAuthMethod.INSTANCE_PROFILE` - EC2 instance profile

Supported services:
- `AWSService.S3` - S3 storage
- `AWSService.EC2` - EC2 compute
- `AWSService.RDS` - RDS databases
- `AWSService.DYNAMODB` - DynamoDB
- `AWSService.LAMBDA` - Lambda functions
- `AWSService.SQS` - Simple Queue Service
- `AWSService.SNS` - Simple Notification Service
- `AWSService.CLOUDWATCH` - CloudWatch monitoring
- `AWSService.IAM` - Identity and Access Management
- `AWSService.SES` - Simple Email Service

### Auth Method Examples

#### Access Key Credentials
```python
config = AWSConnectionConfig(
    name="my-aws",
    region="us-west-2",
    auth_method=AWSAuthMethod.CREDENTIALS,
    aws_access_key_id="your-access-key",
    aws_secret_access_key="your-secret-key",
    service=AWSService.S3
)
```

#### Profile Authentication
```python
config = AWSConnectionConfig(
    name="my-aws",
    region="us-west-2",
    auth_method=AWSAuthMethod.PROFILE,
    profile_name="default",
    service=AWSService.EC2
)
```

#### Role Authentication
```python
config = AWSConnectionConfig(
    name="my-aws",
    region="us-west-2",
    auth_method=AWSAuthMethod.ROLE,
    role_arn="arn:aws:iam::account:role/role-name",
    service=AWSService.LAMBDA
)
```

## Kubernetes Configurations

Kubernetes connections support multiple authentication methods and cluster configurations:

```python
from pangolin_sdk.configs.kubernetes import KubernetesConnectionConfig
from pangolin_sdk.constants import KubernetesAuthMethod, KubernetesResourceType

config = KubernetesConnectionConfig(
    # Common parameters
    name="my-cluster",
    namespace="default",            # Default namespace for operations
    
    # Authentication method
    auth_method=KubernetesAuthMethod.CONFIG,
    
    # For kubeconfig auth
    kubeconfig_path="~/.kube/config",
    context="my-context",          # Optional: specific kubeconfig context
    
    # For token auth
    host="https://kubernetes.default.svc",
    port=6443,
    api_token="your-token",
    
    # For certificate auth
    client_cert_path="/path/to/cert",
    client_key_path="/path/to/key",
    
    # Common options
    ca_cert_path="/path/to/ca",    # CA certificate path
    verify_ssl=True,               # Verify SSL certificates
    in_cluster=False,              # Set True for in-cluster config
    timeout=30,                    # Operation timeout in seconds
)
```

Supported authentication methods:
- `KubernetesAuthMethod.CONFIG` - Kubeconfig file
- `KubernetesAuthMethod.TOKEN` - Service account token
- `KubernetesAuthMethod.CERTIFICATE` - Client certificate
- `KubernetesAuthMethod.BASIC` - Basic authentication

Supported resource types:
- `KubernetesResourceType.POD` - Pods
- `KubernetesResourceType.DEPLOYMENT` - Deployments
- `KubernetesResourceType.SERVICE` - Services
- `KubernetesResourceType.CONFIGMAP` - ConfigMaps
- `KubernetesResourceType.SECRET` - Secrets
- `KubernetesResourceType.NAMESPACE` - Namespaces
- `KubernetesResourceType.NODE` - Nodes
- `KubernetesResourceType.STATEFULSET` - StatefulSets
- `KubernetesResourceType.DAEMONSET` - DaemonSets
- `KubernetesResourceType.INGRESS` - Ingresses
- `KubernetesResourceType.PERSISTENTVOLUME` - PersistentVolumes
- `KubernetesResourceType.PERSISTENTVOLUMECLAIM` - PersistentVolumeClaims

### Auth Method Examples

#### Kubeconfig Authentication
```python
config = KubernetesConnectionConfig(
    name="my-cluster",
    auth_method=KubernetesAuthMethod.CONFIG,
    kubeconfig_path="~/.kube/config",
    context="my-context",
    namespace="default"
)
```

#### Service Account Token Authentication
```python
config = KubernetesConnectionConfig(
    name="my-cluster",
    auth_method=KubernetesAuthMethod.TOKEN,
    host="https://kubernetes.default.svc",
    port=6443,
    api_token="your-service-account-token",
    namespace="default",
    ca_cert_path="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
)
```

#### Certificate Authentication
```python
config = KubernetesConnectionConfig(
    name="my-cluster",
    auth_method=KubernetesAuthMethod.CERTIFICATE,
    host="https://kubernetes.default.svc",
    port=6443,
    client_cert_path="/path/to/client.crt",
    client_key_path="/path/to/client.key",
    ca_cert_path="/path/to/ca.crt",
    namespace="default"
)
```

#### In-Cluster Configuration
```python
config = KubernetesConnectionConfig(
    name="my-cluster",
    auth_method=KubernetesAuthMethod.TOKEN,
    in_cluster=True,              # Automatically use service account token
    namespace="default"
)
```

### Configuration for Different Environments

#### Local Development
```python
config = KubernetesConnectionConfig(
    name="local-dev",
    auth_method=KubernetesAuthMethod.CONFIG,
    kubeconfig_path="~/.kube/config",
    context="minikube",           # For Minikube
    namespace="development"
)
```

#### Production Environment
```python
config = KubernetesConnectionConfig(
    name="production",
    auth_method=KubernetesAuthMethod.TOKEN,
    host="https://prod-cluster.example.com",
    port=6443,
    api_token="your-production-token",
    namespace="production",
    verify_ssl=True,
    timeout=60
)
```

#### Multi-Cluster Configuration
```python
configs = {
    "dev": KubernetesConnectionConfig(
        name="dev-cluster",
        auth_method=KubernetesAuthMethod.CONFIG,
        kubeconfig_path="~/.kube/config",
        context="dev-context",
        namespace="development"
    ),
    "staging": KubernetesConnectionConfig(
        name="staging-cluster",
        auth_method=KubernetesAuthMethod.TOKEN,
        host="https://staging-cluster.example.com",
        api_token="staging-token",
        namespace="staging"
    ),
    "prod": KubernetesConnectionConfig(
        name="prod-cluster",
        auth_method=KubernetesAuthMethod.CERTIFICATE,
        host="https://prod-cluster.example.com",
        client_cert_path="/path/to/prod/client.crt",
        client_key_path="/path/to/prod/client.key",
        namespace="production"
    )
}
```

## Best Practices

1. Always use appropriate authentication methods for your use case
2. Set reasonable timeouts and retry parameters
3. Use SSL/TLS when possible
4. Store sensitive credentials securely
5. Use environment variables or configuration files for credentials
6. Set appropriate logging levels in options
7. Use connection pools for database connections when applicable
8. Implement proper error handling for configuration validation