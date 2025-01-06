from marshmallow import Schema, fields, post_load
from pangolin.ssh_engine import SSH_Engine


class EngineConfigSchema(Schema):
    timeout = fields.Int(default=30)
    logging_enabled = fields.Bool(default=False)
    connection_retries = fields.Int(default=3)


class SSH_EngineSchema(Schema):
    hostname = fields.Str(required=True)
    username = fields.Str(required=True)
    password = fields.Str(allow_none=False)
    private_key = fields.Str(allow_none=False)
    port = fields.Int(default=22)
    config = fields.Nested(EngineConfigSchema)

    @post_load
    def create_ssh_engine(self, data, **kwargs):
        return SSH_Engine(**data)
