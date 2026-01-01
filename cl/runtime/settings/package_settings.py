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
from typing import Mapping
from typing_extensions import final
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import MAPPING_TYPES
from cl.runtime.records.typename import typenameof
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class PackageSettings(Settings):
    """Settings for the package location, dependencies, and requirements."""

    package_dirs: Mapping[str, str] = required()
    """
    Mapping of package (e.g., cl.runtime) to its directory relative to project root.

    Note:
      If the package is directly under project root (e.g. {project_root}\cl\runtime), specify "." as the value.
    """

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if not isinstance(self.package_dirs, MAPPING_TYPES):
            raise RuntimeError(f"Field 'package_dirs' must be a mapping, but got {typenameof(self.package_dirs)}.")

    def get_packages(self) -> tuple[str, ...]:
        """Return package_dirs keys as a tuple, ignoring their directories."""
        return tuple(self.package_dirs.keys())
