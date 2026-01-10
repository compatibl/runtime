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

import datetime as dt
import os
from dataclasses import dataclass
from typing_extensions import final
from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.records.typename import typename
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class LogSettings(Settings):
    """REST API settings."""

    log_type: str = "FileLog"
    """Log type name in ClassName format."""

    log_level: str = "INFO"
    """Log level in UPPERCASE format."""

    log_filename_format: str = "prefix-timestamp"
    """
    Log filename format, the choices are:
    - prefix: Prefix only
    - prefix-timestamp: Prefix followed by UTC timestamp to millisecond precision in dash-delimited format
    """

    log_filename_prefix: str = "default"
    """Log filename prefix."""

    log_filename_timestamp: dt.datetime = DatetimeUtil.now()
    """Timestamp to use for log file, set to the time of program launch if not specified in settings."""

    log_dir: str | None = None
    """Directory for log files (optional, defaults to '{project_root}/logs')."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if not isinstance(self.log_type, str) or not CaseUtil.is_pascal_case(self.log_type):
            raise RuntimeError(f"{typename(type(self))} field 'log_type' must be a string in ClassName format.")

        # Convert logging level to uppercase and validate its values
        self.log_level = self.log_level.upper()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_levels:
            raise RuntimeError(
                f"Invalid log level: {self.log_level}, permitted values are: {', '.join(valid_levels)}. "
                f"Lower, upper or mixed case can be used."
            )

    @classmethod
    def get_log_dir(cls) -> str:
        """Get database directory (optional, defaults to '{project_root}/logs')."""
        if (result := LogSettings.instance().log_dir) is None:
            project_root = ProjectLayout.get_project_root()
            result = os.path.join(project_root, "logs")
        return result
