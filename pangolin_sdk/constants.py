from enum import Enum


class ConnectionStatus(Enum):
    """Connection states for tracking connection lifecycle."""

    INITIALIZED = "initialized"
    VALIDATING = "validating"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class DatabaseType(Enum):
    """Supported database types."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"
    MSSQL = "mssql"
    SQLITE = "sqlite"


class HTTPVerb(Enum):
    """HTTP verbs/methods with descriptions and specifications"""

    GET = "GET"  # Retrieve a resource
    POST = "POST"  # Create a new resource
    PUT = "PUT"  # Update/Replace a resource
    DELETE = "DELETE"  # Delete a resource
    PATCH = "PATCH"  # Partial modification of a resource
    HEAD = "HEAD"  # Same as GET but without response body
    OPTIONS = "OPTIONS"  # Describe communication options
    TRACE = "TRACE"  # Message loop-back test


class AuthMethod(Enum):
    """Supported authentication methods"""

    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    DIGEST = "digest"
    HMAC = "hmac"


class SSHAuthMethod(Enum):
    PASSWORD = "password"
    PUBLIC_KEY = "publickey"
    AGENT = "agent"


class HeaderRequirement(Enum):
    """Header requirement levels"""

    REQUIRED = "required"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"


class ParamikoKey(Enum):
    RSA = "RSA"
    DSS = "DSS"
    ECDSA = "ECDSA"
    ED25519 = "ED25519"

    def __str__(self):
        return self.value


class KubernetesAuthMethod(Enum):
    """Supported Kubernetes authentication methods"""

    NONE = "none"
    BASIC = "basic"
    TOKEN = "token"
    CERTIFICATE = "certificate"
    CONFIG = "config"


class KubernetesResourceType(Enum):
    """Supported Kubernetes resource types"""

    POD = "pod"
    DEPLOYMENT = "deployment"
    SERVICE = "service"
    CONFIGMAP = "configmap"
    SECRET = "secret"
    NAMESPACE = "namespace"
    NODE = "node"
    STATEFULSET = "statefulset"
    DAEMONSET = "daemonset"
    INGRESS = "ingress"
    PERSISTENTVOLUME = "persistentvolume"
    PERSISTENTVOLUMECLAIM = "persistentvolumeclaim"


class KubernetesApiVersion(Enum):
    """Supported Kubernetes API versions"""

    V1 = "v1"
    APPS_V1 = "apps/v1"
    BATCH_V1 = "batch/v1"
    NETWORKING_V1 = "networking.k8s.io/v1"
    STORAGE_V1 = "storage.k8s.io/v1"


class AWSAuthMethod(Enum):
    """Supported AWS authentication methods"""

    ACCESS_KEY = "access_key"
    PROFILE = "profile"
    INSTANCE_ROLE = "instance_role"
    WEB_IDENTITY = "web_identity"
    SSO = "sso"


class AWSService(Enum):
    """Supported AWS services"""

    S3 = "s3"
    EC2 = "ec2"
    RDS = "rds"
    LAMBDA = "lambda"
    DYNAMODB = "dynamodb"
    SQS = "sqs"
    SNS = "sns"
    IAM = "iam"
    CLOUDWATCH = "cloudwatch"
    ECS = "ecs"
    EKS = "eks"
    ROUTE53 = "route53"


class AWSRegion(Enum):
    """AWS Regions"""

    US_EAST_1 = "us-east-1"
    US_EAST_2 = "us-east-2"
    US_WEST_1 = "us-west-1"
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    EU_WEST_2 = "eu-west-2"
    EU_CENTRAL_1 = "eu-central-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"
    AP_SOUTHEAST_2 = "ap-southeast-2"
    AP_NORTHEAST_1 = "ap-northeast-1"
    AP_NORTHEAST_2 = "ap-northeast-2"
    SA_EAST_1 = "sa-east-1"
