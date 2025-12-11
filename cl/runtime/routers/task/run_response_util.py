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

from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_pydantic.pydantic_mixin import PydanticMixin
from cl.runtime.records.protocols import is_sequence_type, is_key_type, is_data_key_or_record_type
from cl.runtime.routers.task.run_request import RunRequest
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.tasks.task_util import TaskUtil
from cl.runtime.views.key_list_view import KeyListView
from cl.runtime.views.key_view import KeyView
from cl.runtime.views.record_list_view import RecordListView
from cl.runtime.views.record_view import RecordView

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

        method_task = tasks[0]

        # TODO (Roman): Use TypeDecl to determine method type
        if method_task.method_name.startswith("view_"):

            # Run task in process
            # TODO (Roman): Check for Dynamic View and load from DB instead of running Task
            result = method_task.run_task_in_process()

            # Process viewer result according to conventions
            result = cls._process_viewer_result(result)

            # Build Data object
            if is_data_key_or_record_type(result):
                result.build()

        else:
            # Run task in process
            result = method_task.run_task_in_process()

        # Serialize Data instances
        # Do not serialize PydanticMixin instances, since it is supported by FastAPI
        if result and not isinstance(result, PydanticMixin) and isinstance(result, DataMixin):
            return _ui_serializer.serialize(result)
        else:
            return result

    @classmethod
    def _process_viewer_result(cls, viewer_result: Any) -> Any:
        """
        Convert viewer result according to conventions.

        The following viewer results are supported:
            - Record or list of records;
            - Key or list of keys;
            - Any View object;
            - None value.
        """

        if is_key_type(type(viewer_result)):
            # Load Key from DB
            return active(DataSource).load_one_or_none(viewer_result)
        elif is_sequence_type(type(viewer_result)):
            # Process items in sequence
            return tuple(cls._process_viewer_result(x) for x in viewer_result)
        elif isinstance(viewer_result, KeyListView):
            # Process KeyListView by unpacking the 'keys' field
            return cls._process_viewer_result(viewer_result.keys)
        elif isinstance(viewer_result, RecordListView):
            # Process RecordListView by unpacking the 'records' field
            return cls._process_viewer_result(viewer_result.records)
        elif isinstance(viewer_result, KeyView):
            # Process KeyView by unpacking the 'key' field
            return cls._process_viewer_result(viewer_result.key)
        elif isinstance(viewer_result, RecordView):
            # Process RecordView by unpacking the 'record' field
            return cls._process_viewer_result(viewer_result.record)
        else:
            # Other types return unchanged
            return viewer_result
