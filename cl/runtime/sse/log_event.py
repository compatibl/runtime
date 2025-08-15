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
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.sse.event import Event


@dataclass(slots=True, kw_only=True)
class LogEvent(Event):
    """Event type with info about log message. Follow the format in which the logs are stored in the database."""

    level: str = required()
    """String level of this message in PascalCase (Debug, Info, Warning, Error, Critical)."""

    message: str = required()
    """A descriptive message providing details about the logging event."""

    readable_time: str | None = None
    """Human-readable time when the log record was created in UTC."""

    record_type_name: str | None = None
    """Type on which the handler is running."""

    handler_name: str | None = None
    """Handler name."""

    record_key: str | None = None
    """Record key."""

    task_run_id: str | None = None
    """Unique task run identifier."""
