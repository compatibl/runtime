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
from cl.runtime.settings.app_env import AppEnv
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
class AppSettings(Settings):
    """Settings for the naming and location of the app data."""

    env: AppEnv | None = None
    """Determines the default settings for multiuser access and data retention."""

    name: str | None = None
    """Identifies the application or test."""

    user: str | None = None
    """Identifies the application or test user."""

    user_scoped: bool | None = None
    """Deployment data is fully isolated for each user if true and shared if false (user must be set either way)."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if self.env is not None:
            # Convert from string to AppEnv enum if necessary
            if isinstance(self.env, str):
                if self.env.islower():
                    # Create enum after converting to uppercase if the string is in lowercase
                    if (item := self.env.upper()) in AppEnv:
                        self.env = AppEnv[item]  # noqa
                    else:
                        valid_items = "\n".join(item.name.lower() for item in AppEnv)
                        raise RuntimeError(
                            f"Enum AppEnv does not include the item {str(self.env)}.\n"
                            f"Valid items are:\n{valid_items}\n"
                        )
                else:
                    raise RuntimeError(f"Invalid environment name {self.env}, it should be lowercase.")
            elif not isinstance(self.env, AppEnv):
                raise RuntimeError(f"The value of env should be a string or an instance of AppEnv.")

    @classmethod
    def get_base_type(cls) -> type:
        return AppSettings
