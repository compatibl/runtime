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

import base64
from typing import List
from uuid import UUID

from pydantic import BaseModel

from cl.runtime.primitive.string_util import StringUtil
from cl.runtime.routers.tasks.task_status_request import TaskStatusRequest
from cl.runtime.serialization.string_serializer import StringSerializer
from cl.runtime.tasks.task_observer import TaskObserver


class TaskStatusResponseItem(BaseModel):
    """Data type for a single item in the response list for the /tasks/run/status route."""

    status_code: int
    """Task status code."""

    task_run_id: str
    """Task run unique id."""

    key: str | None
    """Key of the record."""

    class Config:
        alias_generator = StringUtil.to_pascal_case
        populate_by_name = True

    @staticmethod
    def get_task_statuses(request: TaskStatusRequest) -> List[TaskStatusResponseItem]:
        """Get status for tasks in request."""

        response_items = []
        for run_id_as_str in request.task_run_ids:
            # TODO (Roman): optimize using load_many instead of load_one in TaskObserver.get_status()

            # convert string run_id to UUID and create TaskObserver
            task_observer = TaskObserver(task_run_id=UUID(run_id_as_str))

            key = task_observer.get_key()
            key_serializer = StringSerializer()
            # get status and key from TaskObserver and create response item
            response_items.append(
                TaskStatusResponseItem(
                    status_code=task_observer.get_status(),
                    task_run_id=run_id_as_str,
                    key=key_serializer.serialize_key(key) if key else None,
                ),
            )

        return response_items