"""SSH Connection Configuration Module.

This module provides classes for configuring SSH connections using Paramiko.
"""

import io
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Type

import paramiko

from pangolin_sdk.configs.base import ConnectionConfig
from pangolin_sdk.constants import ParamikoKey, SSHAuthMethod


@dataclass
class ParamikoSSHKeyTypes:
    """Different Key Types supported by Paramiko."""

    key_classes={
            "RSA": paramiko.RSAKey,
            "DSS": paramiko.DSSKey,
            "ECDSA": paramiko.ECDSAKey,
            "ED25519": paramiko.Ed25519Key,
        }

    def get_key(self, key_type: ParamikoKey) -> paramiko.PKey:
        """
        Returns the corresponding key class based on the provided key type.

        Args:
            key_type (ParamikoKey): The type of SSH key to retrieve.

        Returns:
            paramiko.PKey: An instance of the specified key type.

        Raises:
            ValueError: If the key type is not supported.
        """
        key_class = self.key_classes.get(key_type.name)
        if key_class:
            return key_class
        raise ValueError(f"Unsupported key type: {key_type}")


@dataclass(kw_only=True)
class SSHConnectionConfig(ConnectionConfig):
    """Configuration for SSH connections."""

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

    def __post_init__(self) -> None:
        """
        Validate configuration based on the chosen authentication method.

        Raises:
            ValueError: If configuration is invalid for the selected auth method.
        """
        if self.auth_method == SSHAuthMethod.PASSWORD:
            self._validate_password_auth()
        elif self.auth_method == SSHAuthMethod.PUBLIC_KEY:
            self._validate_public_key_auth()
        elif self.auth_method == SSHAuthMethod.AGENT:
            self._validate_agent_auth()
        else:
            raise ValueError(f"Unsupported authentication method: {self.auth_method}")

    def _validate_password_auth(self) -> None:
        """
        Validate password-based authentication requirements.

        Raises:
            ValueError: If username or password is missing.
        """
        if not self.password:
            raise ValueError("Password is required for PASSWORD authentication method.")
        if not self.username:
            raise ValueError("Username is required for PASSWORD authentication method.")

    def _validate_public_key_auth(self) -> None:
        """
        Validate public key authentication requirements.

        Raises:
            ValueError: If required key parameters are missing.
        """
        # Validate key filename or key type is provided
        if not self.key_filename and not self.pkey_type:
            raise ValueError(
                "Either key_filename or pkey_type must be provided for PUBLIC_KEY authentication."
            )

        # Validate encrypted key scenario
        if not self.encrypted_key_str and not self.pkey_type and not self.passphrase:
            raise ValueError(
                "Either encrypted_key_str or pkey_type and passphrase must be provided for PUBLIC_KEY authentication."
            )

        # Load key based on available information
        if self.encrypted_key_str and self.pkey_type:
            self.load_encrypted_private_key()
        elif self.key_filename and self.pkey_type:
            self.load_pkey_using_file()

    def _validate_agent_auth(self) -> None:
        """
        Validate SSH agent authentication requirements.

        Raises:
            ValueError: If username is missing.
        """
        if not self.username:
            raise ValueError("Username is required for AGENT authentication method.")

    def load_pkey_using_file(self) -> None:
        """
        Load the private key from a file.

        Raises:
            ValueError: If the key file cannot be loaded or does not exist.
        """
        # If pkey is already set, no need to load
        if self.pkey:
            return

        # Validate key file exists
        if not self.key_filename:
            raise ValueError("No key filename provided.")

        if not os.path.exists(self.key_filename):
            raise ValueError(f"Private key file {self.key_filename} does not exist.")

        try:
            key_class = ParamikoSSHKeyTypes().get_key(self.pkey_type)
            self.private_key = key_class.from_private_key_file(
                self.key_filename, password=self.passphrase
            )
        except paramiko.ssh_exception.SSHException as ssh_error:
            raise ValueError(f"Failed to load private key: {ssh_error}") from ssh_error

    def load_encrypted_private_key(self) -> None:
        """
        Load an encrypted private key from a string.

        Raises:
            ValueError: If the key cannot be decrypted or loaded.
        """
        if not self.encrypted_key_str:
            raise ValueError("No encrypted key string provided.")

        # Convert the encrypted private key string to a file-like object
        key_file = io.StringIO(self.encrypted_key_str)

        # Load the encrypted private key using Paramiko
        try:
            key_class = ParamikoSSHKeyTypes().get_key(self.pkey_type)
            self.private_key = key_class.from_private_key(
                key_file, password=self.passphrase
            )
        except paramiko.PasswordRequiredException as pwd_error:
            raise ValueError("The passphrase is incorrect or missing.") from pwd_error
        except Exception as load_error:
            raise ValueError(
                f"Failed to load the private key: {load_error}"
            ) from load_error
