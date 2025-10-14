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

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass

from cl.runtime.db.tenant import Tenant
from cl.runtime.db.tenant_key import TenantKey
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.tasks.task_queue_key import TaskQueueKey


@dataclass(slots=True, kw_only=True)
class TaskQueue(TaskQueueKey, ABC):
    """
    Run a query on tasks, run all returned tasks sequentially or in parallel, then repeat.

    Notes:
        - A task may run sequentially or in parallel with other tasks
        - A task may run in a different process, thread or machine than the submitting code
          and must be able to acquire the required resources to run in all of these scenarios
        - The queue updates 'status' field of the task as it progresses from its initial Pending state through
          the Running and optionally Paused state and ending in one of Completed, Failed, or Cancelled states
    """

    tenant: TenantKey = required()
    """Tenant within the TaskQueue (initialized to the common tenant if not specified)."""

    timeout_sec: int = 10
    """Optional timeout in seconds, queue will stop after reaching this timeout."""

    def __init(self):
        # Use globally unique UUIDv7-based timestamp if not specified
        if self.queue_id is None:
            self.queue_id = Timestamp.create()

        if self.tenant is None:
            self.tenant = Tenant.get_common()

    def get_key(self) -> TaskQueueKey:
        return TaskQueueKey(queue_id=self.queue_id).build()

    @abstractmethod
    def run_start_queue(self) -> None:
        """Run a query on tasks, run all returned tasks sequentially or in parallel, then repeat."""

    @abstractmethod
    def run_stop_queue(self) -> None:
        """Exit after completing all currently executing tasks."""
