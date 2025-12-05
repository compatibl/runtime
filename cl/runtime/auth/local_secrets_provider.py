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

import pathlib
import uuid
from dataclasses import dataclass
from datetime import datetime
import ruamel.yaml
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.secrets.secrets_provider import SecretsProvider
from cl.runtime.file.project_layout import ProjectLayout


@dataclass(slots=True, kw_only=True)
class LocalSecretsProvider(SecretsProvider):
    """Retrieve secrets from local file based vault."""

    path_to_secrets: str = "keys/"
    """Path to .secrets.yaml file."""

    def add_secret(self, name: str, value, *, content_type: str | None = None) -> None:
        data = self._load_secrets()
        new_secret = {
            uuid.uuid4().hex: {
                "content_type": content_type,
                "created": DatetimeUtil.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "enabled": True,
                "value": value,
            }
        }
        if data.get(name) is not None:
            data.get(name).update(new_secret)
        else:
            data[name] = new_secret
        self._save_secrets(data)
        return

    def get_secret(self, name: str) -> dict[str, str]:
        data = self._load_secrets()

        versions = data.get(name)
        if not versions:
            raise ValueError(f"No versions found for secret '{name}'.")

        # filter disabled secrets
        versions = dict(filter(lambda item: item[1]["enabled"], versions.items()))

        latest_version = max(
            versions.items(), key=lambda item: datetime.fromisoformat(item[1]["created"].replace("Z", "+00:00"))
        )

        version, _ = latest_version
        return {
            "value": versions[version]["value"],
            "version": version,
        }

    def get_secret_by_version(self, name: str, version: str) -> dict[str, str]:
        data = self._load_secrets()

        versions = data.get(name)
        if not versions:
            raise ValueError(f"No versions found for secret '{name}'.")

        if not versions.get(version, {}).get("enabled", False):
            raise ValueError(f"Version '{version}' not enabled for secret '{name}'.")

        return {
            "value": versions[version]["value"],
            "version": version,
        }

    def _get_secrets_dir(self) -> pathlib.Path:
        return pathlib.Path(ProjectLayout.get_project_root()).joinpath(pathlib.Path(self.path_to_secrets))

    def _load_secrets(self) -> dict[str, dict]:
        secrets_path = self._get_secrets_dir() / ".secrets.yaml"
        try:
            result = ruamel.yaml.YAML(typ="safe", pure=True).load(secrets_path.read_text())
            if result is None:
                return {}
            return result
        except FileNotFoundError:
            return {}

    def _save_secrets(self, secrets_dict: dict[str, dict]) -> None:
        secrets_path = self._get_secrets_dir() / ".secrets.yaml"
        if not secrets_path.exists():
            secrets_path.parent.mkdir(parents=True, exist_ok=True)
        ruamel.yaml.YAML().dump(secrets_dict, secrets_path)
