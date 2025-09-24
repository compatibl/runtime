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
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.typename import typename
from cl.runtime.routers.tasks.submit_request import SubmitRequest
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.tasks.celery.celery_queue import CeleryQueue
from cl.runtime.tasks.class_method_task import ClassMethodTask
from cl.runtime.tasks.instance_method_task import InstanceMethodTask
from cl.runtime.tasks.method_task import MethodTask
from cl.runtime.tasks.task import Task

handler_queue = CeleryQueue(queue_id="Handler Queue")

_ui_serializer = DataSerializers.FOR_UI


class TaskUtil:
    """Utilities for working with tasks."""

    @classmethod
    def _deserialize_request_args(cls, request_args: dict[str, Any], task: MethodTask) -> dict[str, Any]:
        """Deserialize request task arguments from UI format using type hints from method definition."""

        if request_args is None:
            return dict()

        # Get specific task type hints
        arg_type_hints = task.get_method_arg_type_hints()

        # Deserialize values in argument dict
        return {
            k: _ui_serializer.deserialize(v, arg_type_hints.get(k))
            for k_, v in request_args.items()
            if (k := CaseUtil.pascal_to_snake_case(k_))
        }

    @classmethod
    def create_tasks_for_submit_request(cls, request: SubmitRequest) -> list[Task]:
        """Create Task objects from task submit request."""

        # TODO: Refactor
        # TODO (Roman): request [None] for static handlers explicitly
        # Workaround for static handlers
        requested_keys = request.keys if request.keys else [None]

        # Normalize handler name to handler functions naming format
        handler_name = cls._normalize_handler_name(request.method)

        tasks = []

        for serialized_key in requested_keys:

            # Create handler task
            # TODO: Add request.arguments_ and type_
            if serialized_key is not None:
                # Key is not None, this is an instance method

                record_type = TypeInfo.from_type_name(request.type)
                key_type = record_type.get_key_type()
                key = KeySerializers.DELIMITED.deserialize(serialized_key, TypeHint.for_type(key_type))

                label = f"{typename(key_type)};{serialized_key};{handler_name}"
                handler_task = InstanceMethodTask(
                    label=label,
                    queue=handler_queue.get_key(),
                    key=key,
                    method_name=handler_name,
                )

                # Deserialize request args from UI format
                handler_task.method_args = cls._deserialize_request_args(request.arguments, handler_task)  # noqa

                tasks.append(handler_task.build())
            else:
                # Key is None, this is a @classmethod or @staticmethod
                record_type = TypeInfo.from_type_name(request.type)
                label = f"{typename(record_type)};{handler_name}"
                handler_task = ClassMethodTask(
                    label=label,
                    queue=handler_queue.get_key(),
                    type_=record_type,
                    method_name=handler_name,
                )

                # Deserialize request args from UI format
                handler_task.method_args = cls._deserialize_request_args(request.arguments, handler_task)  # noqa

                tasks.append(handler_task.build())

        return tasks

    @classmethod
    def _normalize_handler_name(cls, handler_name: str) -> str:
        """Normalize handler name to snake case, prefixed with 'run_'."""
        if not CaseUtil.is_snake_case(handler_name):
            try:
                handler_name = CaseUtil.pascal_to_snake_case(handler_name)
            except RuntimeError:
                raise RuntimeError(f"Invalid handler name format: '{handler_name}'.")
        handler_name = f"run_{handler_name}"
        return handler_name
