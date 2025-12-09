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

from typing import Self

from pydantic import BaseModel
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.routers.task.submit_request import SubmitRequest
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.tasks.instance_method_task import InstanceMethodTask
from cl.runtime.tasks.task_queue import TaskQueue
from cl.runtime.tasks.task_util import TaskUtil


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
    def get_response(cls, request: SubmitRequest) -> list[Self]:
        """Submit tasks and return list of task response items."""

        response_items = []
        task_queue = active(TaskQueue)

        for handler_task in TaskUtil.create_tasks_for_submit_request(request):

            # Save and submit task
            active(DataSource).replace_one(handler_task, commit=True)
            task_queue.submit_task(handler_task)  # TODO: Rely on query instead

            if isinstance(handler_task, InstanceMethodTask):
                # Only InstanceMethodTask has `key` field
                key = KeySerializers.DELIMITED.serialize(handler_task.key)
            else:
                key = None

            response_items.append(SubmitResponseItem(key=key, task_run_id=handler_task.task_id))

        return response_items
