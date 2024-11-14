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
from typing_extensions import Self
from cl.runtime import RecordMixin
from cl.runtime.log.log_message_key import LogMessageKey
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.dataclasses_extensions import missing


@dataclass(slots=True, kw_only=True)
class LogMessage(LogMessageKey, RecordMixin[LogMessageKey]):
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

    def get_key(self) -> LogMessageKey:
        return LogMessageKey(timestamp=self.timestamp)

    def init(self) -> Self:
        """Similar to __init__ but can use fields set after construction, return self to enable method chaining."""

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
                raise ValueError(f"Invalid logging level: {self.level}. Valid choices are:"
                                 f"Debug, Info, Warning, Error, Critical")

        if self.message is None:
            self.message = "An error occurred. Contact technical support for assistance."

        # Return self to enable method chaining
        return self
