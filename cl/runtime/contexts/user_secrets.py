# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import logging
from dataclasses import dataclass
from typing import Dict
from typing import Any
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cl.runtime.contexts.context_manager import active_or_default
from cl.runtime.contexts.utils.user_secrets_util import UserSecretsUtil
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin

_LOGGER = logging.getLogger(__name__)

def populate_user_secrets_from_scope(scope: Dict[str, Any]) -> dict[str, str]:
    """Extract user keys from ASGI scope headers with 'cl-user-key-*' prefix."""

    user_keys: dict[str, str] = {}

    raw_headers = scope.get("headers") or []
    prefix = b"cl-user-key-"

    for name, value in raw_headers:
        name_lower = name.lower()
        if name_lower.startswith(prefix):
            key = name_lower[len(prefix):].decode()
            user_keys[key] = value.decode()

    return user_keys


@dataclass(slots=True, kw_only=True)
class UserSecrets(DataclassMixin):
    """User-specific settings and data."""

    encrypted_secrets: dict[str, str] | None = None
    """User secrets specified here take precedence over those defined via Dynaconf."""

    @classmethod
    def get_key_type(cls) -> type:  # TODO: Remove after deriving from RecordMixin
        return UserSecrets

    def decrypt_secret(self, secret_name: str) -> str | None:
        """Decrypt the specified secret in UserSecrets, None if no active UserSecrets or the secret is not found."""

        # Get secrets field of the current user secrets context, return None if not specified
        user_secrets = active_or_default(UserSecrets)
        if user_secrets is None or ((encrypted_secrets := user_secrets.encrypted_secrets) is None):
            return None

        secret_name_in_ui_format = secret_name.replace('_', '-').lower()
        # Get secret by key, return None if key is not present
        encrypted_value = encrypted_secrets.get(secret_name_in_ui_format)
        if encrypted_value is None:
            _LOGGER.info(
                f"UserSecrets.decrypt_secret: secret with key '{secret_name}' is not found.",
            )
            return None

        # Decode base64 encoded encrypted value
        encrypted_value_bytes = base64.b64decode(encrypted_value)

        # Load the private key
        # Temporary minimal private cert support
        private_key: RSAPrivateKey = UserSecretsUtil.get_rsa_private_key()

        # Decrypt the value
        decrypted_value_bytes = private_key.decrypt(
            encrypted_value_bytes,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )

        return decrypted_value_bytes.decode("utf-8")
