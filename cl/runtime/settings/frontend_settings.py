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
from typing_extensions import final  # TODO: Replace by the import from typing
from cl.runtime.prebuild.version_util import VersionUtil
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class FrontendSettings(Settings):
    """Settings that apply to the static frontend files."""

    frontend_version: str | None = None
    """Install a specific frontend version in MAJOR.MINOR.MICRO format."""

    frontend_download_uri: str = "https://github.com/compatibl/frontend/archive/refs/tags/{version}"
    """URI template for frontend download (if file extension is omitted, .zip and .tar.gz options will be provided)."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Validate that version string is in CompatibL CalVer format if specified
        if self.frontend_version is not None:
            VersionUtil.guard_version_string(self.frontend_version)

        # Validate that frontend_download_uri contains the {version} parameter
        if "{version}" not in self.frontend_download_uri:
            raise ValueError("The setting for frontend_download_uri must contain the '{version}' parameter.")

    def get_frontend_download_uri_templates(self) -> tuple[str, ...]:
        """Get the list of frontend URIs based on the specified template."""

