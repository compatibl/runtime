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

from frozendict import frozendict
from typing_extensions import final

from cl.runtime.prebuild.version_format import VersionFormat
from cl.runtime.records.protocols import is_mapping_type
from cl.runtime.settings.settings import Settings
from cl.runtime.settings.settings_util import SettingsUtil


@dataclass(slots=True, kw_only=True)
@final
class VersionSettings(Settings):
    """Version settings."""

    version_format: VersionFormat = VersionFormat.CAL_VER
    """Default version format applies when exception is not specified for the module."""

    version_format_exceptions: Mapping[str, VersionFormat] = frozendict({"cl.runtime.routers": VersionFormat.SEM_VER})
    """Version format exceptions for individual modules, overrides the default format."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Convert to enum if specified
        self.version_format = SettingsUtil.to_enum(self.version_format, enum_type=VersionFormat)

        # Convert each value to enum
        if is_mapping_type(type(self.version_format_exceptions)):
            self.version_format_exceptions = frozendict({
                k: SettingsUtil.to_enum(v, enum_type=VersionFormat)
                for k, v in self.version_format_exceptions.items()
            })
        else:
            raise RuntimeError(f"VersionSettings.version_format_exceptions is not a mapping.")


