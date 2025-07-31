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
from cl.runtime.log.log_message import LogMessage
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.tasks.task_status import TaskStatus


@dataclass(slots=True, kw_only=True)
class TaskLogs(DataMixin):
    """Class with aggregated logs for single task."""

    task_run_id: str = required()
    """Unique task run identifier."""

    record_type: str = required()
    """Record Type on which handler is run."""

    handler_name: str = required()
    """Handler name."""

    record_key: str | None = None
    """Record key on which handler is run."""

    status: TaskStatus | None = None
    """Task status."""

    logs: list[LogMessage] | None = None
    """Task logs."""
