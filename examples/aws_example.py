from pangolin_sdk.configs.aws import AWSConnectionConfig
from pangolin_sdk.constants import AWSAuthMethod, AWSService, AWSRegion
from pangolin_sdk.connections.aws import AWSConnection

# Create config
config = AWSConnectionConfig(
    name="my-aws",
    auth_method=AWSAuthMethod.ACCESS_KEY,
    service=AWSService.S3,
    region=AWSRegion.US_EAST_1,
    access_key_id="your-key",
    secret_access_key="your-secret",
)

# Create connection
aws = AWSConnection(config)

# Execute operations (connect is handled automatically)
result = aws.execute(operation="list_buckets", using="client")

# Get results
buckets = aws.get_last_result()

# Clean up
aws.disconnect()
