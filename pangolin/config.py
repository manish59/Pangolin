from marshmallow import Schema, fields, post_load


class PangolinConfig:
    """Default configuration for the SDK."""

    DEFAULT_TIMEOUT = 30
    LOGGING_ENABLED = True
    CONNECTION_RETRIES = 3
