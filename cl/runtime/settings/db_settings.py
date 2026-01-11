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
from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.typename import typename, typenameof
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class DbSettings(Settings):
    """Database settings."""

    db_id: str = required()  # TODO: Allow f-string parameters
    """Database identifier as string or Python f-string."""

    db_type: str = required()  # TODO: !! Refactor to use to_object from settings
    """Database class name."""

    db_client_uri: str = required()
    """URI provided to the database client."""

    db_username: str | None = None
    """Username provided to the database client."""

    db_password: str | None = None
    """Password provided to the database client."""

    db_name_separator: str | None = None
    """Separator for the tokens in database name."""

    db_dev_prefix: str = "dev_"
    """DB WITH THIS PREFIX IS DELETED ON EVERY BACKEND PROCESS START *** WITH *** USER APPROVAL."""

    db_temp_prefix: str = "temp_"
    """DB WITH THIS PREFIX IS DELETED ON EVERY BACKEND PROCESS START *** WITHOUT *** USER APPROVAL."""

    db_test_prefix: str = "test_"
    """DB WITH THIS PREFIX IS DELETED BEFORE AND AFTER EVERY UNIT TEST *** WITHOUT *** USER APPROVAL."""

    db_dir: str | None = None
    """Directory for database files (optional, defaults to '{project_root}/databases')."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if self.db_id is None:
            raise RuntimeError(f"Field 'db_name' in settings.yaml is missing.")
        elif not isinstance(self.db_id, str):
            raise RuntimeError(f"Field 'db_name' in settings.yaml must be None or a string.")

        if not isinstance(self.db_type, str):
            # TODO: Check the class is valid
            raise RuntimeError(f"{typename(type(self))} field 'db_type' must be Db class name in PascalCase format.")

        if self.db_client_uri is None:
            # Use default client URI protocol, hostname and port depending on the database type
            if self.db_type.endswith("MongoDb"):
                uri_prefix = "mongodb://"
                uri_suffix = "localhost:27017/"
            elif self.db_type.endswith("CouchDb"):
                uri_prefix = "http://"
                uri_suffix = "localhost:5984/"
            else:
                raise RuntimeError(
                    f"{typenameof(self)}.db_client_uri is not set and no\n"
                    f"suitable default exists for db_type={self.db_type}."
                )
            # Substitute username and password if specified
            if self.db_username is not None and self.db_password is not None:
                self.db_client_uri = f"{uri_prefix}{self.db_username}:{self.db_password}@{uri_suffix}"
            elif self.db_username is not None:
                self.db_client_uri = f"{uri_prefix}{self.db_username}@{uri_suffix}"
            else:
                self.db_client_uri = f"{uri_prefix}{uri_suffix}"

        if self.db_name_separator is None:
            # Set the separator symbol based on the database type
            if self.db_type.endswith("MongoDb"):
                self.db_name_separator = ";"
            elif self.db_type.endswith("CouchDb"):
                self.db_name_separator = "/"
            else:
                raise RuntimeError(
                    f"{typenameof(self)}.db_name_separator is not set and no\n"
                    f"suitable default exists for db_type={self.db_type}."
                )

    @classmethod
    def get_db_dir(cls) -> str:
        """Get database directory (optional, defaults to '{project_root}/databases')."""
        if (result := DbSettings.instance().db_dir) is None:
            project_root = ProjectLayout.get_project_root()
            result = os.path.join(project_root, "databases")
        return result
