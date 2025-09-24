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

from dataclasses import dataclass
from types import FunctionType
from types import MethodType
from typing import Callable
from typing import Self
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.log.task_log import TaskLog
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.typename import typenameof
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.tasks.method_task import MethodTask
from cl.runtime.tasks.task_queue_key import TaskQueueKey

_KEY_SERIALIZER = KeySerializers.DELIMITED


@dataclass(slots=True, kw_only=True)
class InstanceMethodTask(MethodTask):
    """Invoke a class instance method, do not use for @classmethod or @staticmethod."""

    key: KeyMixin = required()
    """Key of the record for which the method is invoked."""

    def get_method_callable(self) -> FunctionType | MethodType:
        # Load record from Db
        record = active(DataSource).load_one(self.key)

        return getattr(record, self.method_name)

    def _create_log_context(self) -> TaskLog:
        """Create TaskLog with task specific info."""
        return TaskLog(
            record_type_name=typenameof(self.key),
            handler=self._title_handler_name(self.method_name),
            task_run_id=self.task_id,
            record_key=KeySerializers.DELIMITED.serialize(self.key),
        ).build()

    @classmethod
    def create(
        cls,
        *,
        queue: TaskQueueKey,
        key: KeyMixin,
        method_callable: Callable,
    ) -> Self:
        """
        Create from the record or its key and an instance-bound or class-bound method callable.

        Notes:
            - The key is required if the callable is for a class rather than an instance.

        Args:
            queue: Queue that will run the task
            key: Key of the instance for which the method is invoked
            method_callable: Callable bound to a class (ClassName.method_name) or its instance (obj.method_name)
        """

        # Populate known fields
        result = cls(queue=queue, key=key)

        # Two tokens because the callable is bound to a class or its instance
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
        result.label = (
            f"{KeySerializers.DELIMITED.serialize(key, TypeHint.for_type(KeyMixin))};{method_name_pascal_case}"
        )
        return result
