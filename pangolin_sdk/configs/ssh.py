from dataclasses import dataclass, field
from typing import Optional
import paramiko
import os
import io
from pangolin_sdk.constants import SSHAuthMethod, ParamikoKey
from pangolin_sdk.configs.base import ConnectionConfig


@dataclass
class ParamikoSSHKeyTypes:
    key_classes = {
        "RSA": paramiko.RSAKey,
        "DSS": paramiko.DSSKey,
        "ECDSA": paramiko.ECDSAKey,
        "ED25519": paramiko.Ed25519Key,
    }

    def get_key(self, key_type: ParamikoKey) -> paramiko.PKey:
        """
        Returns the corresponding key class based on the provided key type.
        """
        key_class = self.key_classes.get(key_type)
        if key_class:
            return key_class()
        else:
            raise ValueError(f"Unsupported key type: {key_type}")


@dataclass(kw_only=True)
class SSHConnectionConfig(ConnectionConfig):
    """Configuration for SSH connections"""

    key_filename: Optional[str] = None
    pkey: Optional[paramiko.RSAKey] = None
    pkey_type: ParamikoKey = field(default_factory=lambda: ParamikoKey.RSA)
    allow_agent: bool = True
    auth_method: SSHAuthMethod = SSHAuthMethod.PASSWORD
    port: int = 22
    private_key: Optional[str] = None
    look_for_keys: bool = True
    host_key_policy: str = "auto"
    sock: Optional[str] = None
    banner_timeout: int = 15
    passphrase: Optional[str] = None
    agent_path: Optional[str] = None
    encrypted_key_str: Optional[str] = None

    def __post_init__(self):
        # Validation based on the chosen authentication method
        if self.auth_method == SSHAuthMethod.PASSWORD:
            if not self.password:
                raise ValueError(
                    "Password is required for PASSWORD authentication method."
                )
            if not self.username:
                raise ValueError(
                    "Username is required for PASSWORD authentication method."
                )

        elif self.auth_method == SSHAuthMethod.PUBLIC_KEY:
            if not self.key_filename and not self.pkey_type:
                raise ValueError(
                    "Either key_filename or pkey_type must be provided for PUBLIC_KEY authentication."
                )
            if (
                not self.encrypted_key_str
                and not self.pkey_type
                and not self.passphrase
            ):
                raise ValueError(
                    "Either encrypted_key_str or pkey_type and passphrase must be provided for PUBLIC_KEY authentication."
                )

            if self.encrypted_key_str and self.passphrase and self.pkey_type:
                self.load_encrypted_private_key()
            elif self.key_filename and self.pkey_type:
                self.load_pkey_using_file()
        elif self.auth_method == SSHAuthMethod.AGENT:
            if not self.username:
                raise ValueError(
                    "Username is required for AGENT authentication method."
                )
            # SSH Agent does not require password or key to be explicitly set

        else:
            raise ValueError(
                f"Unsupported authentication method: {self.auth_method}")

    def load_pkey_using_file(self):
        """
        Loads the private key either from the filename or directly if pkey is provided.
        :return: Loaded private key or None if the key cannot be loaded.
        """
        if self.pkey:
            print("Using provided pkey object.")
            return self.pkey

        if self.key_filename:
            if not os.path.exists(self.key_filename):
                raise ValueError(
                    f"Private key file {self.key_filename} does not exist."
                )
            try:
                key_class = ParamikoSSHKeyTypes().get_key(self.key_type)
                self.private_key = key_class.from_private_key_file(
                    self.key_filename, password=self.passphrase
                )
            except paramiko.ssh_exception.SSHException:
                pass  # If DSS failed, try ECDSA

        raise ValueError("No private key provided via key_filename or pkey.")

    def load_encrypted_private_key(self) -> None:
        """
        Load an encrypted private key from a string and return a Paramiko key object.

        :param encrypted_key_str: The encrypted private key as a string
        :param passphrase: The passphrase used to decrypt the key
        :return: A paramiko.RSAKey or another key object
        """
        # Convert the encrypted private key string to a file-like object
        key_file = io.StringIO(self.encrypted_key_str)

        # Load the encrypted private key using Paramiko
        try:
            key_class = ParamikoSSHKeyTypes().get_key(self.pkey_type)
            self.private_key = key_class.from_private_key(
                key_file, password=self.passphrase
            )
        except paramiko.PasswordRequiredException:
            raise ValueError("The passphrase is incorrect or missing.")
        except Exception as e:
            raise ValueError(f"Failed to load the private key: {e}")
