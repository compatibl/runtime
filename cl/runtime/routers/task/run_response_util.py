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

from typing import Any

from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_pydantic.pydantic_mixin import PydanticMixin
from cl.runtime.routers.task.run_request import RunRequest
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.tasks.task_util import TaskUtil

_ui_serializer = DataSerializers.FOR_UI


class RunResponseUtil:
    """Response util for the /task/run route."""

    @classmethod
    def get_response(cls, request: RunRequest) -> Any:
        """Run Task and return result as response."""

        # Create Task from Request data
        tasks = TaskUtil.create_tasks(
            type_name=request.type,
            method_name=request.method,
            args=request.arguments,
            str_keys=[request.key] if request.key else None,
        )

        if len(tasks) != 1:
            raise RuntimeError(
                f"It is expected that there will be only one Task for RunResponse. "
                f"Actual number of tasks: {len(tasks)}."
            )

        task = tasks[0]

        # Run task in process
        result = task.run_task_in_process()

        # Serialize Data instances
        # Do not serialize PydanticMixin instances, since it is supported by FastAPI
        if result and not isinstance(result, PydanticMixin) and isinstance(result, DataMixin):
            return _ui_serializer.serialize(result)
        else:
            return result