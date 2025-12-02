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

from dataclasses import dataclass

from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.settings.settings import Settings
from cl.runtime.settings.settings_util import SettingsUtil


@dataclass(slots=True, kw_only=True)
class SecretsSettings(Settings):
    """Settings for secrets management."""

    secrets_path: str = "keys"
    """Path to store secrets defined relative to resources root."""

    secrets_provider_type_name: str | None = None
    """Secrets provider type name."""

    _secrets_provider: DataMixin | None = None
    """Secrets provider instance if specified (type hint is not specified to avoid a cyclic reference)."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        # Create a SecretsProvider instance
        self._secrets_provider = SettingsUtil.to_object_or_none(settings=self, prefix="secrets_provider")

    def get_secrets_provider_or_none(self) -> DataMixin | None:
        """Get secrets provider instance (type hint is not specified to avoid a cyclic reference)."""
        return self._secrets_provider
