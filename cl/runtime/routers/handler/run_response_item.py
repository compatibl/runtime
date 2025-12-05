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
from typing import Self
from cl.runtime.contexts.context_manager import activate
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_pydantic.pydantic_mixin import PydanticMixin
from cl.runtime.routers.tasks.submit_request import SubmitRequest
from cl.runtime.auth.user_secrets import UserSecrets
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.tasks.task_util import TaskUtil

# Create serializers
_UI_SERIALIZER = DataSerializers.FOR_UI


class RunResponseItem(PydanticMixin):
    """Response item for the /handler/run route."""

    result: Any
    """Run result."""

    @classmethod
    def get_response(cls, request: SubmitRequest) -> list[Self]:

        # Enter user secrets context
        with activate(UserSecrets(encrypted_secrets=request.user_keys).build()):

            results = []
            for handler_task in TaskUtil.create_tasks_for_submit_request(request):
                # Run task as callable in main process
                handler_result = handler_task.run_task_in_process()
                if (
                    handler_result
                    and not isinstance(handler_result, PydanticMixin)
                    and isinstance(handler_result, DataMixin)
                ):
                    # Serialize data instances
                    handler_result = _UI_SERIALIZER.serialize(handler_result)
                results.append(cls(result=handler_result))

            return results
