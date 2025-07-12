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
from cl.runtime.records.conditions import Condition
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.tasks.task import Task
from cl.runtime.tasks.task_queue_key import TaskQueueKey
from cl.runtime.tasks.task_status import TaskStatus


@dataclass(slots=True, kw_only=True)
class TaskQuery(QueryMixin):
    """Query for Task by the queue and status fields."""

    queue: TaskQueueKey = required()
    """The queue that will run the task once it is saved."""

    status: TaskStatus | Condition[TaskStatus] | None = None
    """Begins from Pending, continues to Running or Paused, and ends with Completed, Failed, or Cancelled."""

    @classmethod
    def get_target_type(cls) -> type:
        return Task
