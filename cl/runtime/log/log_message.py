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
from cl.runtime import RecordMixin
from cl.runtime.log.log_message_key import LogMessageKey
from cl.runtime.primitive.timestamp import Timestamp


@dataclass(slots=True, kw_only=True)
class LogMessage(LogMessageKey, RecordMixin):
    """
    Refers to a record that captures specific information
    about events or actions occurring within an application.
    """

    level: str | None = None
    """String level of this message in PascalCase (Debug, Info, Warning, Error, Critical)."""

    priority: int | None = None
    """Numerical priority of this message as an integer from 1 (Debug) to 5 (Critical)."""

    message: str | None = None
    """A descriptive message providing details about the logging event."""

    logger_name: str | None = None
    """Name of the logger that produced log record."""

    readable_time: str | None = None
    """Human-readable time when the log record was created in UTC."""

    traceback: str | None = None
    """Traceback."""

    record_type: str | None = None
    """Type on which the handler is running."""

    handler_name: str | None = None
    """Handler name."""

    record_key: str | None = None
    """Record key."""

    task_run_id: str | None = None
    """Task run id."""

    def get_key(self) -> LogMessageKey:
        return LogMessageKey(timestamp=self.timestamp).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Set timestamp
        if self.timestamp is None:
            self.timestamp = Timestamp.create()

        # Default to Error if not set
        if self.level is None:
            self.level = "Error"

        # Validate level and set numerical priority
        match self.level:
            case "Debug":
                self.priority = 1
            case "Info":
                self.priority = 2
            case "Warning":
                self.priority = 3
            case "Error":
                self.priority = 4
            case "Critical":
                self.priority = 5
            case _:
                raise ValueError(
                    f"Invalid logging level: {self.level}. Valid choices are:" f"Debug, Info, Warning, Error, Critical"
                )

        if self.message is None:
            self.message = "An error occurred. Contact technical support for assistance."
