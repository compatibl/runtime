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

from __future__ import annotations
from typing import Iterable
from typing import cast
from pydantic import BaseModel
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.routers.tasks.status_request import StatusRequest
from cl.runtime.tasks.instance_method_task import InstanceMethodTask
from cl.runtime.tasks.task import Task
from cl.runtime.tasks.task_key import TaskKey

LEGACY_TASK_STATUS_NAMES_MAP: dict[str, str] = {  # TODO: Update UI to sync the status list
    "PENDING": "Submitted",
    "RUNNING": "Running",
    "AWAITING": "Paused",
    "COMPLETED": "Completed",
    "FAILED": "Failed",
    "CANCELLED": "Cancelled",
}
"""Status name to legacy status name map according to UI convention."""


class StatusResponseItem(BaseModel):
    """Response data type for the /tasks/status route."""

    task_run_id: str
    """Task run id."""

    status_code: str
    """Task status."""

    key: str | None = None
    """Key string in semicolon-delimited format."""

    user_message: str | None = None
    """Optional user message."""

    class Config:
        alias_generator = CaseUtil.snake_to_pascal_case
        populate_by_name = True

    @classmethod
    def get_response(cls, request: StatusRequest) -> list[StatusResponseItem]:
        """Get status for tasks in request."""

        task_keys = [TaskKey(task_id=x).build() for x in request.task_run_ids]  # TODO: Update if task_run_id is UUID
        tasks = cast(Iterable[Task], DbContext.load_many(Task, task_keys))

        response_items = []
        for task in tasks:
            # TODO: Add support message depending on exception type.
            user_message = task.error_message

            key = None

            # Only InstanceMethodTask has `key_str` attribute.
            if isinstance(task, InstanceMethodTask):
                key = task.key_str

            response_items.append(
                StatusResponseItem(
                    status_code=LEGACY_TASK_STATUS_NAMES_MAP.get(task.status.name),
                    task_run_id=str(task.task_id),
                    key=key,
                    user_message=user_message,
                ),
            )

        return response_items
