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
from typing_extensions import final
from cl.runtime.file.project_layout import ProjectLayout
from cl.runtime.prebuild.version_util import VersionUtil
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class FrontendSettings(Settings):
    """Settings that apply to the static frontend files."""

    frontend_version: str | None = None
    """Install a specific frontend version in MAJOR.MINOR.MICRO format."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        # Validate version string format if specified
        if self.frontend_version is not None:
            VersionUtil.guard_version_string(self.frontend_version)
