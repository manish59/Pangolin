from pangolin_sdk.configs.kubernetes import KubernetesConnectionConfig
from pangolin_sdk.constants import KubernetesAuthMethod, KubernetesResourceType
from pangolin_sdk.connections.kubernetes import KubernetesConnection

# Create config
config = KubernetesConnectionConfig(
    name="my-cluster",
    auth_method=KubernetesAuthMethod.CONFIG,
    kubeconfig_path="~/.kube/config",
    namespace="default",
)

# Create connection
k8s = KubernetesConnection(config)

# Execute operations (connect is handled automatically)
result = k8s.execute(
    resource_type=KubernetesResourceType.POD, action="list", namespace="default"
)

# Get results
pods = k8s.get_last_result()

# Clean up
k8s.disconnect()
