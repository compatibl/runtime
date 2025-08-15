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

import os
from dataclasses import dataclass
from typing_extensions import final
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.typename import typename
from cl.runtime.settings.project_settings import ProjectSettings
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class DbSettings(Settings):
    """Database settings."""

    db_id: str = required()  # TODO: Allow f-string parameters
    """Database identifier as string or Python f-string."""

    db_type: str = required()
    """Database class name."""

    db_uri: str | None = None
    """Database URI (optional, defaults to a local database file or localhost)."""

    db_test_prefix: str = "test_"
    """
    Prefix for unit test databases that are created and deleted automatically.

    Notes:
        DROPPING THE DATABASE AUTOMATICALLY AS PART OF A UNIT TEST WILL FAIL
        UNLESS DB_ID STARTS FROM THIS PREFIX
    """

    db_temp_prefix: str = "temp_"
    """
    Prefix for temporary databases that are created automatically but require explicit user approval to delete.

    Notes:
        DROPPING THE DATABASE FROM CODE OR REST API REQUIRES EXPLICIT USER APPROVAL,
        AND WILL FAIL EVEN WITH APPROVAL UNLESS DB_ID STARTS FROM THIS PREFIX
    """

    db_dir: str | None = None
    """Directory for database files (optional, defaults to '{project_root}/databases')."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if self.db_id is None:
            raise RuntimeError(f"Field 'db_name' in settings.yaml is missing.")
        elif not isinstance(self.db_id, str):
            raise RuntimeError(f"Field 'db_name' in settings.yaml must be None or a string.")

        if not isinstance(self.db_type, str):
            raise RuntimeError(f"{typename(self)} field 'db_type' must be Db class name in PascalCase format.")

    @classmethod
    def get_db_dir(cls) -> str:
        """Get database directory (optional, defaults to '{project_root}/databases')."""
        if (result := DbSettings.instance().db_dir) is None:
            project_root = ProjectSettings.get_project_root()
            result = os.path.join(project_root, "databases")
        return result
