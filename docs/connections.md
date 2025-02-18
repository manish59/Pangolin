# Pangolin SDK Connections Documentation

This guide explains how to use different connection types in the Pangolin SDK, including database, API, and SSH connections.

## Connection Lifecycle

All connections in Pangolin SDK provide these key methods:

1. `connect()`: Establishes the connection and returns a connection handler (optional as execute() handles this automatically)
2. `execute()`: Automatically establishes connection if needed, then runs operations
3. `disconnect()`: Cleans up and deletes the connection object
4. Result retrieval: Use `get_last_result()` or `get_results()` to access execution results

Note: You don't need to call connect() explicitly as execute() will handle the connection automatically. However, you should always call disconnect() when you're done.

## Database Connections

### Configuration

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
```

### Usage Example

```python
from pangolin_sdk.connections.database import DatabaseConnection

# Create connection instance
db = DatabaseConnection(config)

# Establish connection - returns SQLAlchemy session
session = db.connect()

# Execute query
db.execute(
    "SELECT * FROM users WHERE age > :age",
    params={"age": 25}
)

# Get results
last_result = db.get_last_result()  # Get most recent query results
all_results = db.get_results()      # Get all query results

# Clean up
db.disconnect()
```

## API Connections

### Configuration

```python
from pangolin_sdk.configs.api import APIConfig
from pangolin_sdk.constants import AuthMethod

config = APIConfig(
    name="my-api",
    host="https://api.example.com",
    auth_method=AuthMethod.BEARER,
    auth_token="your-token"
)
```

### Usage Example

```python
from pangolin_sdk.connections.api import APIConnection

# Create connection instance
api = APIConnection(config)

# Establish connection - returns requests.Session
session = api.connect()

# Execute request
api.execute(
    method="POST",
    endpoint="/users",
    data={"name": "John Doe"}
)

# Get results
last_response = api.get_last_result()  # Get most recent API response
all_responses = api.get_results()       # Get all API responses

# Clean up
api.disconnect()
```

## SSH Connections

### Configuration

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
```

### Usage Example

```python
from pangolin_sdk.connections.ssh import SSHConnection

# Create connection instance
ssh = SSHConnection(config)

# Establish connection - returns paramiko.SSHClient
client = ssh.connect()

# Execute command
ssh.execute("ls -la")

# Get results
last_output = ssh.get_last_result()  # Get most recent command output
all_outputs = ssh.get_results()      # Get all command outputs

# Clean up
ssh.disconnect()
```

## Connection Details

### Connection Handlers
Each connection type returns a different connection handler from `connect()`:
- Database: Returns a SQLAlchemy session
- API: Returns a requests.Session
- SSH: Returns a paramiko.SSHClient

### Result Retrieval
All connections provide two methods for accessing results:
- `get_last_result()`: Returns the most recent execution result
- `get_results()`: Returns a list of all execution results since connection

### Returned Results by Connection Type
- Database: Returns rows as OrderedDict
- API: Returns dict with status_code, headers, and response data
- SSH: Returns command output as string

## Error Handling

```python
try:
    # Execute operations (connection is handled automatically)
    connection.execute(...)
    
    # Get results
    result = connection.get_last_result()
    
except ConnectionError as e:
    print(f"Connection failed: {e.message}")
    print(f"Details: {e.details}")
    print(f"Timestamp: {e.timestamp}")
    
except ExecutionError as e:
    print(f"Execution failed: {e.message}")
    
finally:
    # Always clean up
    connection.disconnect()
```

## Connection States

Connections can be in the following states (ConnectionStatus):
- INITIALIZED: Initial state after creation
- VALIDATING: During validation
- CONNECTING: During connection attempt
- CONNECTED: Successfully connected
- DISCONNECTING: During disconnect
- DISCONNECTED: Successfully disconnected
- ERROR: Error state

Check the current state using:
```python
status = connection.get_status()
```

## Kubernetes Connections

### Configuration

Kubernetes connections support multiple authentication methods through the `KubernetesConnectionConfig` class:

```python
from pangolin_sdk.configs.kubernetes import KubernetesConnectionConfig
from pangolin_sdk.constants import KubernetesAuthMethod

config = KubernetesConnectionConfig(
    name="my-cluster",
    auth_method=KubernetesAuthMethod.CONFIG,
    kubeconfig_path="~/.kube/config",  # For CONFIG auth method
    namespace="default",
    
    # For TOKEN auth method
    host="kubernetes.default.svc",
    port=6443,
    api_token="your-token",
    
    # For CERTIFICATE auth method
    client_cert_path="/path/to/cert",
    client_key_path="/path/to/key",
    
    # Common options
    ca_cert_path="/path/to/ca",
    verify_ssl=True,
    context="my-context",    # Optional: specific kubeconfig context
    in_cluster=False        # Set True for in-cluster config
)
```

Supported authentication methods:
- Config File (`KubernetesAuthMethod.CONFIG`)
- Service Account Token (`KubernetesAuthMethod.TOKEN`)
- Client Certificate (`KubernetesAuthMethod.CERTIFICATE`)
- Basic Auth (`KubernetesAuthMethod.BASIC`)

### Usage Example

```python
from pangolin_sdk.connections.kubernetes import KubernetesConnection
from pangolin_sdk.constants import KubernetesResourceType

# Create connection
k8s = KubernetesConnection(config)

# Execute operations (handles connection automatically)
result = k8s.execute(
    resource_type=KubernetesResourceType.POD,
    action="list",
    namespace="default"
)

# Get operation results
pods = k8s.get_last_result()
all_results = k8s.get_results()

# Perform other operations
k8s.execute(
    resource_type=KubernetesResourceType.DEPLOYMENT,
    action="create",
    body={
        "metadata": {"name": "nginx"},
        "spec": {
            "replicas": 3,
            "template": {
                "metadata": {"labels": {"app": "nginx"}},
                "spec": {
                    "containers": [{
                        "name": "nginx",
                        "image": "nginx:latest"
                    }]
                }
            }
        }
    }
)

# Clean up
k8s.disconnect()
```

### Supported Resource Types
Available through `KubernetesResourceType` enum:
- Pod (`POD`)
- Deployment (`DEPLOYMENT`)
- Service (`SERVICE`)
- ConfigMap (`CONFIGMAP`)
- Secret (`SECRET`)
- Namespace (`NAMESPACE`)
- Node (`NODE`)
- StatefulSet (`STATEFULSET`)
- DaemonSet (`DAEMONSET`)
- Ingress (`INGRESS`)
- PersistentVolume (`PERSISTENTVOLUME`)
- PersistentVolumeClaim (`PERSISTENTVOLUMECLAIM`)

### Common Operations
The `execute()` method supports standard Kubernetes operations:
- `list`: List resources
- `get`: Get a specific resource
- `create`: Create a new resource
- `delete`: Delete a resource
- `patch`: Partially update a resource
- `replace`: Replace a resource
- `watch`: Watch for resource changes

## Best Practices

1. Keep it simple - let execute() handle connections:
   ```python
   connection = Connection(config)
   try:
       connection.execute(...)  # Handles connection automatically
       results = connection.get_last_result()
   finally:
       connection.disconnect()
   ```

2. Use context managers when possible
3. Always call disconnect() in a finally block
4. Check connection status before operations
5. Use error handling for robust applications