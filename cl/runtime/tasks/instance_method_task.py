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
from typing import Callable
from typing_extensions import Self
from typing_extensions import override
from cl.runtime import TypeImport
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import is_record
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.tasks.method_task import MethodTask
from cl.runtime.tasks.task_queue_key import TaskQueueKey

_KEY_SERIALIZER = KeySerializers.DELIMITED


@dataclass(slots=True, kw_only=True)
class InstanceMethodTask(MethodTask):
    """Invoke a class instance method, do not use for @classmethod or @staticmethod."""

    key_type_str: str = required()
    """Key type as dot-delimited string in module.ClassNameKey format inclusive of Key suffix if present."""

    key_str: str = required()
    """Key as semicolon-delimited string."""

    @override
    def _execute(self) -> None:
        """Invoke the specified instance method."""

        key_type = TypeImport.class_from_qual_name(self.key_type_str)
        type_hint = TypeHint.for_class(key_type)
        key = _KEY_SERIALIZER.deserialize(self.key_str, type_hint)

        # Load record from storage
        record = DbContext.load_one(key_type, key)  # TODO: Require record type?

        # Convert the name to snake_case and get method callable
        method_name = self.normalized_method_name()
        method = getattr(record, method_name)

        params = self.deserialized_method_params()
        method(**params)

    @classmethod
    def create(
        cls,
        *,
        queue: TaskQueueKey,
        record_or_key: KeyProtocol | None = None,
        method_callable: Callable,
    ) -> Self:
        """
        Create from the record or its key and an instance-bound or class-bound method callable.

        Notes:
            - The key is required if the callable is for a class rather than an instance.

        Args:
            queue: Queue that will run the task
            record_or_key: Record or its key
            method_callable: Callable bound to a class (ClassName.method_name) or its instance (obj.method_name)
        """

        # Populate known fields
        result = cls(queue=queue)

        # Get key type and key
        key_type = record_or_key.get_key_type()
        result.key_type_str = f"{key_type.__module__}.{TypeUtil.name(key_type)}"
        key = record_or_key.get_key() if is_record(record_or_key) else record_or_key
        result.key_str = _KEY_SERIALIZER.serialize(key)

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
        result.label = f"{TypeUtil.name(key_type)};{result.key_str};{method_name_pascal_case}"
        return result
