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

import inspect
from dataclasses import dataclass
from typing import Callable
from typing_extensions import Self
from typing_extensions import override
from cl.runtime import TypeImport
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.tasks.method_task import MethodTask
from cl.runtime.tasks.task_queue_key import TaskQueueKey


@dataclass(slots=True, kw_only=True)
class StaticMethodTask(MethodTask):
    """Invoke a @staticmethod or @classmethod, do not use for instance methods."""

    type_str: str = required()
    """Class type as dot-delimited string in module.ClassName format."""

    @override
    def _execute(self) -> None:
        """Invoke the specified @staticmethod or @classmethod."""

        # Get record type from fully qualified name in module.ClassName format
        record_type = TypeImport.get_class_from_qual_name(self.type_str)

        # Method callable is already bound to cls, it is not necessary to pass cls as an explicit parameter
        method_name = self.normalized_method_name()
        method = getattr(record_type, method_name)

        params = self.deserialized_method_params()
        method(**params)

    @classmethod
    def create(
        cls,
        *,
        queue: TaskQueueKey,
        record_type: type,
        method_callable: Callable,
    ) -> Self:
        """Create from @staticmethod callable and record type."""

        # Populate known fields
        result = cls(queue=queue)
        result.type_str = f"{record_type.__module__}.{TypeUtil.name(record_type)}"

        # Check that __self__ is either absent (@staticmethod) or is a class (@classmethod)
        if (method_cls := getattr(method_callable, "__self__", None)) is not None and not inspect.isclass(method_cls):
            raise RuntimeError(
                f"Callable '{method_callable.__qualname__}' for task_id='{result.task_id}' is "
                f"an instance method rather than @staticmethod or @classmethod, "
                f"use 'InstanceMethodTask' instead of 'StaticMethodTask'."
            )

        # Two tokens because the callable is bound to a class
        method_tokens = method_callable.__qualname__.split(".")
        if len(method_tokens) == 2:
            # Second token is method name
            result.method_name = method_tokens[1]
        else:
            raise RuntimeError(
                f"Callable '{method_callable.__qualname__}' for task_id='{result.task_id}' does not "
                f"have two dot-delimited tokens indicating it is not a method bound to a class."
            )

        # Set label and return
        method_name_pascal_case = CaseUtil.snake_to_pascal_case(result.method_name)
        result.label = f"{TypeUtil.name(record_type)};{method_name_pascal_case}"
        return result
