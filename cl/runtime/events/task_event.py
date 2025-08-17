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
from cl.runtime.contexts.context_manager import active_or_none
from cl.runtime.events.event import Event
from cl.runtime.log.task_log import TaskLog
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class TaskEvent(Event):
    """Event type with info about Task."""

    task_run_id: str = required()
    """Unique task run identifier."""

    record_type_name: str = required()
    """Record Type on which handler is run."""

    handler_name: str = required()
    """Handler name."""

    record_key: str | None = None
    """Record key on which handler is run."""

    def __init(self):
        if self.task_run_id is None:
            log_context = active_or_none(TaskLog)

            if log_context is None:
                raise RuntimeError("TaskEvent can only be created inside a TaskLog.")

            if log_context.task_run_id is None:
                raise RuntimeError("TaskLog.task_run_id is required to create TaskEvent.")

            if log_context.record_type_name is None:
                raise RuntimeError("TaskLog.type is required to create TaskEvent.")

            if log_context.handler is None:
                raise RuntimeError("TaskLog.handler is required to create TaskEvent.")

            # Fill in Event fields from Context
            self.task_run_id = log_context.task_run_id
            self.record_type_name = log_context.record_type_name
            self.handler_name = log_context.handler
            self.record_key = log_context.record_key
