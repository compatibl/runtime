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
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from types import FunctionType
from types import MethodType
from typing_extensions import Any
from typing_extensions import override
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.json_encoders import JsonEncoders
from cl.runtime.tasks.task import Task

_json_serializer = DataSerializers.FOR_JSON


@dataclass(slots=True, kw_only=True)
class MethodTask(Task, ABC):
    """Base class for method tasks that invoke handlers from classes."""

    method_name: str = required()
    """The name of method in snake_case format."""

    method_args: str | None = None
    """Encoded method args as a JSON string. Use 'self.decode_args()' method to get dict."""

    def __init(self):
        # Encode method_args to str if assigned dict
        if isinstance(self.method_args, dict):
            if self.method_args:
                type_hints = self.get_method_arg_type_hints()
                encoded_args = self._encode_args(self.method_args, type_hints)
                self.method_args = encoded_args
            else:
                self.method_args = None

    @abstractmethod
    def get_method_callable(self) -> FunctionType | MethodType:
        """Get method callable for Task."""
        raise NotImplementedError()

    @override
    def _execute(self):
        """Invoke the specified instance method."""

        # Get method callable
        method = self.get_method_callable()

        # Get args dict
        args = self.decode_args()

        # Run method
        return method(**args)

    def get_method_arg_type_hints(self) -> dict[str, TypeHint]:
        """Return method argument type hints."""

        method_callable = self.get_method_callable()
        signature = inspect.signature(method_callable)

        # Create TypeHint objects from signature params
        return {
            name: TypeHint.for_type_alias(type_alias=param.annotation, containing_type=self.__class__, field_name=name)
            for name, param in signature.parameters.items()
            if param.annotation != inspect.Parameter.empty
        }

    def decode_args(self) -> dict[str, Any]:
        """Decode and deserialize task method arguments to dict format."""

        if self.method_args is None:
            return {}

        # Get method type hints
        type_hints = self.get_method_arg_type_hints()

        # Decode str arguments to dict
        serialized_args = JsonEncoders.COMPACT.decode(self.method_args)

        # Deserialize dict method arguments using method type hints
        return {k: _json_serializer.deserialize(v, type_hints.get(k)) for k, v in serialized_args.items()}

    @classmethod
    def _encode_args(cls, args: dict[str, Any], type_hints: dict[str, TypeHint]) -> str:
        """Serialize and encode method args in dict format to str."""

        # Serialize dict arguments using method type hints
        serialized_args = {k: _json_serializer.serialize(v, type_hints.get(k)) for k, v in args.items()}

        # Encode serialized args from dict to str
        return JsonEncoders.COMPACT.encode(serialized_args)

    @classmethod
    def _title_handler_name(cls, handler_name: str) -> str:
        """Remove 'run_' prefix and convert to title case."""
        # TODO (Roman): Fix handler name in schema
        handler_name = handler_name.removeprefix("run_")
        handler_title = CaseUtil.snake_to_title_case(handler_name)
        return handler_title
