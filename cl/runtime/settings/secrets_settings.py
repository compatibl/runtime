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
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
class SecretsSettings(Settings):  # TODO: !!!! Rename to SecretsSettings (plural)
    """Settings for secrets management."""

    secrets_enable: bool | None = None
    """Enable user secrets (requires managing user key in the client)."""

    secrets_path: str = "keys"
    """Path to store secrets defined relative to resources root."""

    secrets_provider: dict[str, str] = None  # TODO: !!!! Refactor to avoid a dict
    """Secrets provider configuration."""

    def __init(self):
        if self.secrets_provider is None:
            self.secrets_provider = {"type": "LocalSecretsProvider"}  # TODO: !!!! Refactor to avoid type name
