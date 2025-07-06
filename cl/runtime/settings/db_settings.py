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
from typing import Tuple
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
class DbSettings(Settings):
    """Database settings."""

    name: str = required()  # TODO: Allow f-string parameters
    """Database name as string or Python f-string."""

    type: str = required()
    """Database class name."""

    uri: str | None = None
    """Database URI (optional, defaults to a local database file or localhost)."""

    temp_prefix: str = "temp_"
    """
    IMPORTANT: DELETING ALL RECORDS AND DROPPING THE DATABASE FROM CODE IS PERMITTED
    only when database name starts with this prefix (optional, defaults to 'temp_').
    """

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if self.name is None:
            raise RuntimeError(f"Field 'db_name' in settings.yaml is missing.")
        elif not isinstance(self.name, str):
            raise RuntimeError(f"Field 'db_name' in settings.yaml must be None or a string.")

        if not isinstance(self.type, str):
            raise RuntimeError(
                f"{TypeUtil.name(self)} field 'db_type' must be a string in module.ClassName format."
            )

    @classmethod
    def get_base_type(cls) -> type:
        return DbSettings
