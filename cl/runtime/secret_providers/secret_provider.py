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

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Self
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.settings.secret_settings import SecretSettings


@dataclass(slots=True, kw_only=True)
class SecretProvider(DataclassMixin, ABC):
    """Class to provide access to secrets."""

    @classmethod
    def create(cls) -> Self:
        """Create Secret Provider from settings."""

        provider_config_dict = SecretSettings.instance().secret_provider

        # Transform frozendict from settings to dict to get and remove provider type from data
        provider_config_dict = dict(provider_config_dict)
        provider_type = provider_config_dict.pop("type")
        if provider_type is None:
            raise RuntimeError(
                f"Attribute 'type' is required in Secret Provider config. Invalid config:\n {provider_config_dict}"
            )

        return TypeInfo.from_type_name(provider_type)(**provider_config_dict).build()

    @abstractmethod
    def add_secret(self, name: str, value) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_secret(self, secret_name: str) -> dict[str, str]:
        """
        Get last version of secret from vault

        Args:
            secret_name (str): secret name

        Returns:
            dict: {"value": <secret value>, "version": <secret version>}
        """
        raise NotImplementedError()

    @abstractmethod
    def get_secret_by_version(self, secret_name: str, version: str) -> dict[str, str]:
        """
        Get specified version of secret from vault

        Args:
            secret_name (str): secret name
            version (str): secret version

        Returns:
            dict: {"value": <secret value>, "version": <secret version>}
        """
        raise NotImplementedError()

    def get_rsa_private_key(self, secret_name: str, version: str | None = None) -> RSAPrivateKey:
        if version:
            private_key_str = self.get_secret_by_version(secret_name, version)["value"]
        else:
            private_key_str = self.get_secret(secret_name)["value"]

        return serialization.load_pem_private_key(private_key_str.encode(), password=None, backend=default_backend())

    @classmethod
    def get_rsa_public_key(cls, private_key: RSAPrivateKey) -> str:
        public_key_obj = private_key.public_key()
        public_key = public_key_obj.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return public_key.decode()
