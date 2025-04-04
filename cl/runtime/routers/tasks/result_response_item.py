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

from typing import Any, cast, Iterable

from pydantic import BaseModel

from cl.runtime.contexts.db_context import DbContext
from cl.runtime.routers.tasks.result_request import ResultRequest
from cl.runtime.tasks.task import Task
from cl.runtime.tasks.task_key import TaskKey


class ResultResponseItem(BaseModel):
    """Response data type for the /tasks/result route."""

    task_run_id: str
    """Task run id."""

    key: str
    """Key string in semicolon-delimited format."""

    result: Any
    """Task result."""

    @classmethod
    def get_response(cls, request: ResultRequest) -> list[ResultResponseItem]:
        """Get results for tasks in request."""

        task_keys = [TaskKey(task_id=x).build() for x in request.task_run_ids]
        tasks = cast(Iterable[Task], DbContext.load_many(Task, task_keys))

        response_items = []
        for task in tasks:
            response_items.append(
                ResultResponseItem(
                    result=task.status,
                    task_run_id=str(task.task_id),
                    key=str(task.task_id),
                ),
            )

        return response_items