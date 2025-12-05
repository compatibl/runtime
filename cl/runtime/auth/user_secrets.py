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
from typing import cast
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cl.runtime.contexts.context_manager import active_or_default
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.secrets.secrets_provider import SecretsProvider
from cl.runtime.settings.secrets_settings import SecretsSettings

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class UserSecrets(DataclassMixin):
    """User-specific settings and data."""

    encrypted_secrets: dict[str, str] | None = None
    """User secrets specified here take precedence over those defined via Dynaconf."""

    @classmethod
    def get_key_type(cls) -> type:  # TODO: Remove after deriving from RecordMixin
        return UserSecrets

    @classmethod
    def decrypt_secret(cls, secret_name: str) -> str | None:
        """Decrypt the specified secret in UserContext, None if no active UserContext or the secret is not found."""

        # Get secrets field of the current user secrets context, return None if not specified
        user_secrets = active_or_default(
            UserSecrets
        )  # TODO: !! Convert UserSecrets to record to compare identity by key
        if user_secrets is None or ((encrypted_secrets := user_secrets.encrypted_secrets) is None):
            return None

        # TODO (Roman): Align secrets format
        secret_name_in_ui_format = secret_name.replace("_", "-").lower()

        # Get secret by key, return None if key is not present
        encrypted_value = encrypted_secrets.get(secret_name_in_ui_format)
        if encrypted_value is None:
            _LOGGER.debug(
                f"UserSecrets.decrypt_secret: secret with key '{secret_name}' is not found.",
            )
            return None

        # Decode base64 encoded encrypted value
        encrypted_value_bytes = base64.b64decode(encrypted_value)

        # Load the private key
        secrets_settings = SecretsSettings.instance()
        secrets_provider = cast(SecretsProvider, secrets_settings.get_secrets_provider_or_none())
        private_key: RSAPrivateKey = secrets_provider.get_rsa_private_key("USER-SECRETS-PRIVATE-CERT")

        # Decrypt the value
        decrypted_value_bytes = private_key.decrypt(
            encrypted_value_bytes,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )

        return decrypted_value_bytes.decode("utf-8")
