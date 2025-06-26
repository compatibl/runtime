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
from pydantic import BaseModel
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.routers.tasks.submit_request import SubmitRequest
from cl.runtime.tasks.instance_method_task import InstanceMethodTask
from cl.runtime.tasks.task_util import TaskUtil
from cl.runtime.tasks.task_util import handler_queue


class SubmitResponseItem(BaseModel):
    """Response data type for the /tasks/submit route."""

    class Config:
        alias_generator = CaseUtil.snake_to_pascal_case
        populate_by_name = True

    task_run_id: str
    """Task run identifier."""

    key: str | None
    """Key string in semicolon-delimited format."""

    @classmethod
    def get_response(cls, request: SubmitRequest) -> list[SubmitResponseItem]:
        """Submit tasks and return list of task response items."""

        response_items = []

        for handler_task in TaskUtil.create_tasks_for_submit_request(request):

            # Save and submit task
            DbContext.save_one(handler_task)
            handler_queue.submit_task(handler_task)  # TODO: Rely on query instead

            key = handler_task.key_str if isinstance(handler_task, InstanceMethodTask) else None
            response_items.append(SubmitResponseItem(key=key, task_run_id=handler_task.task_id))

        return response_items
