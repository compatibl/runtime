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
from cl.runtime.contexts.context_manager import active_or_none
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.tasks.class_method_task import ClassMethodTask
from cl.runtime.tasks.instance_method_task import InstanceMethodTask
from cl.runtime.tasks.method_task import MethodTask
from cl.runtime.tasks.task import Task
from cl.runtime.tasks.task_queue import TaskQueue
from cl.runtime.tasks.task_queue_key import TaskQueueKey

_ui_serializer = DataSerializers.FOR_UI


class TaskUtil:
    """Utilities for working with tasks."""

    @classmethod
    def _deserialize_task_args(cls, args: dict[str, Any], task: MethodTask) -> dict[str, Any]:
        """Deserialize request task arguments from UI format using type hints from method definition."""

        if args is None:
            return dict()

        # Get specific task type hints
        arg_type_hints = task.get_method_arg_type_hints()

        # Deserialize values in args dict
        return {
            k: _ui_serializer.deserialize(v, arg_type_hints.get(k))
            for k_, v in args.items()
            if (k := CaseUtil.pascal_to_snake_case(k_))
        }

    @classmethod
    def create_tasks(cls, *, type_name: str, method_name: str, str_keys: list[str] | None, args: dict[str, Any] | None) -> list[MethodTask]:

        # TODO (Roman): Make 'queue' field in Task optional
        task_queue_key = task_queue.get_key() if (task_queue := active_or_none(TaskQueue)) else TaskQueueKey(queue_id="Handlers Queue").build()
        type_ = TypeInfo.from_type_name(type_name)

        # Create single ClassMethodTask if keys is not specified
        # TODO (Roman): Consider bulk run for static tasks
        if not str_keys:
            label = f"{typename(type_)};{method_name}"
            static_task = ClassMethodTask(
                label=label,
                queue=task_queue_key,
                type_=type_,
                method_name=method_name,
            )

            # Deserialize method args in UI format
            static_task.method_args = cls._deserialize_task_args(args, static_task)  # noqa

            # Return wrapped in list
            return [static_task.build()]

        # Create list of InstanceMethodTask's for keys
        else:
            # Get Key type for deserialization
            key_type = type_.get_key_type()

            # Deserialize Keys and create InstanceMethodTask's
            instance_tasks = [
                InstanceMethodTask(
                    label=f"{typename(key_type)};{str_key};{method_name}",
                    queue=task_queue_key,
                    key=KeySerializers.DELIMITED.deserialize(str_key, TypeHint.for_type(key_type)),
                    method_name=method_name,
                )
                for str_key in str_keys
            ]

            # Deserialize method args in UI format
            # Do this for each task, since serialization depends on type hints that may change in subclasses
            for instance_task in instance_tasks:
                instance_task.method_args = cls._deserialize_task_args(args, instance_task)  # noqa
                instance_task.build()

            return instance_tasks