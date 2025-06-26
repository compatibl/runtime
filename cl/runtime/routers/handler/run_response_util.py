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

from typing_extensions import Any
from cl.runtime.routers.tasks.submit_request import SubmitRequest
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.tasks.task_util import TaskUtil

# Create serializers
_UI_SERIALIZER = DataSerializers.FOR_UI


class RunResponseUtil:
    """Response util for the /handler/run route."""

    @classmethod
    def get_response(cls, request: SubmitRequest) -> list[Any]:

        results = []
        for handler_task in TaskUtil.create_tasks_for_submit_request(request):
            # Run task as callable in main process
            handler_result = handler_task.run_task_in_process()
            results.append(handler_result)

        return results
