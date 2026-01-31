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
from typing import Sequence
from typing_extensions import final

from cl.runtime.project.project_checks import ProjectChecks
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class BuildSettings(Settings):
    """Settings for the build process."""

    build_dependencies: Sequence[str] | None = None
    """List of dependencies for the build process (defaults to the standard hatch build dependencies)."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Initialize and validate package dependencies
        if self.build_dependencies is None:
            self.build_dependencies = []  # TODO: Add hatch dependencies
        ProjectChecks.guard_requirements(self.build_dependencies)
