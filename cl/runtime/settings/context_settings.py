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
class ContextSettings(Settings):
    """Default context parameters."""

    context_id: str | None = None
    """Context identifier, if not specified a time-ordered UUID will be used."""

    packages: Tuple[str, ...] = required()
    """List of packages to load in dot-delimited format, for example 'cl.runtime' or 'stubs.cl.runtime'."""

    log_class: str = "cl.runtime.log.file.file_log.FileLog"  # TODO: Deprecated, switch to class-specific fields
    """Default log class in module.ClassName format."""

    db_class: str = required()  # TODO: Deprecated, switch to class-specific fields
    """Default database class in module.ClassName format."""

    db_temp_prefix: str = "temp;"
    """
    IMPORTANT: DELETING ALL RECORDS AND DROPPING THE DATABASE FROM CODE IS PERMITTED
    when both db_id and database name start with this prefix.
    """

    db_uri: str | None = None
    """Optional database URI to connect to the database. Required for basic mongo db data source."""

    trial: str | None = None
    """String identifier of the running trial."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if self.context_id is not None and not isinstance(self.context_id, str):
            raise RuntimeError(f"{TypeUtil.name(self)} field 'context_id' must be None or a string.")

        # Convert to tuple
        # TODO: Move to TupleUtil class
        if self.packages is None:
            raise RuntimeError(f"No packages are specified in {TypeUtil.name(self)}, specify at least one.")
        elif isinstance(self.packages, tuple):
            pass
        elif hasattr(self.packages, "__iter__"):
            # Convert all iterable types other than tuple itself to tuple
            self.packages = tuple(self.packages)
        elif isinstance(self.packages, str):
            # Convert string to tuple
            self.packages = (self.packages,)
        else:
            raise RuntimeError(f"Field '{TypeUtil.name(self)}.packages' must be a string or an iterable of strings.")

        # Check that each element is a string
        if package_errors := [
            (
                f"Element at index {index} of field '{TypeUtil.name(self)}.packages is not a string:\n"
                f"Value: {element} Type: {TypeUtil.name(element)})\n"
                if not isinstance(element, str)
                else f"Element at index {index} of field '{TypeUtil.name(self)} is an empty string.\n"
            )
            for index, element in enumerate(self.packages)
            if not isinstance(element, str) or element == ""
        ]:
            raise ValueError("".join(package_errors))

        if not isinstance(self.log_class, str):
            raise RuntimeError(
                f"{TypeUtil.name(self)} field 'log_class' must be a string " f"in module.ClassName format."
            )
        if not isinstance(self.db_class, str):
            raise RuntimeError(
                f"{TypeUtil.name(self)} field 'db_class' must be a string " f"in module.ClassName format."
            )

    @classmethod
    def get_base_type(cls) -> type:
        return ContextSettings
