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
import re
from abc import ABC
from collections import namedtuple
from dataclasses import dataclass
from types import FunctionType
from types import MethodType
from typing import Dict
from inflection import underscore
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.for_dataclasses.extensions import optional
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.tasks.callable_task import CallableTask

_UI_SERIALIZER = DataSerializers.FOR_UI

# Named tuple for method param details
ParamDetails = namedtuple("ParamDetails", ["annot", "default"])


@dataclass(slots=True, kw_only=True)
class MethodTask(CallableTask, ABC):
    """Base class for method tasks that invoke handlers from classes."""

    method_name: str = required()
    """The name of @staticmethod in snake_case or PascalCase format."""

    method_params: dict[str, str] | None = optional(default_factory=lambda: {})  # TODO: Allow values other than string
    """Values for task arguments, if any."""

    def normalized_method_name(self) -> str:
        """If method name has uppercase letters, assume it is PascalCase and convert to snake_case."""
        result = self.method_name
        if any(c.isupper() for c in result):
            # Use inflection library
            result = underscore(result)
            # In addition, add underscore before numbers
            result = re.sub(r"([0-9]+)", r"_\1", result)

        return result

    @classmethod
    def _get_method_param_details(cls, method_callable: FunctionType | MethodType) -> dict[str, ParamDetails]:
        """For a given method/function, extract a dictionary of parameter names to param details."""

        signature = inspect.signature(method_callable)
        param_details = {
            name: ParamDetails(param.annotation, param.default)
            for name, param in signature.parameters.items()
            if param.annotation != inspect.Parameter.empty
        }

        return param_details

    def deserialized_method_params(self, method_callable: FunctionType | MethodType) -> dict:
        """For every method's param - deserialize its value and assign back to it's param name."""

        if not self.method_params:
            return dict()

        # Convert names back to snake_case
        params = {
            CaseUtil.pascal_to_snake_case(param_name): param_value
            for param_name, param_value in self.method_params.items()
        }

        # Get param details from method callable
        param_details = self._get_method_param_details(method_callable)

        # Deserialize each param value
        for param_name, param_value in params.items():

            # Create TypeHint for parameter
            type_hint = (
                TypeHint.for_type_alias(
                    type_alias=_param_details.annot, containing_type=self.__class__, field_name=param_name
                )
                if (_param_details := param_details.get(param_name)) is not None
                else None
            )

            param_value = _UI_SERIALIZER.deserialize(param_value, type_hint=type_hint)

            # Assign deserialized value instead of dict
            params[param_name] = param_value

        return params

    @classmethod
    def _title_handler_name(cls, handler_name: str) -> str:
        """Remove 'run_' prefix and convert to title case."""
        # TODO (Roman): Fix handler name in schema
        handler_name = handler_name.removeprefix("run_")
        handler_title = CaseUtil.snake_to_title_case(handler_name)
        return handler_title
