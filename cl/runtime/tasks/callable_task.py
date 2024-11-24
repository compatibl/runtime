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
import re
from abc import ABC
from dataclasses import dataclass

from inflection import underscore

from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.serialization.ui_dict_serializer import UiDictSerializer
from cl.runtime.tasks.task import Task

data_serializer = UiDictSerializer()


@dataclass(slots=True, kw_only=True)
class CallableTask(Task, ABC):
    """Base class for tasks that invoke callables (class methods, functions, etc.)."""

    @classmethod
    def normalize_method_name(cls, method_name: str) -> str:
        """If method name has uppercase letters, assume it is PascalCase and convert to snake_case."""

        if any(c.isupper() for c in method_name):
            # Use inflection library
            result = underscore(method_name)
            # In addition, add underscore before numbers
            result = re.sub(r"([0-9]+)", r"_\1", result)
        else:
            # Already in snake_case, return unchanged argument
            result = method_name
        return result

    @staticmethod
    def deserialize_method_params(method_params: dict) -> dict:
        """For every method's param - deserialize its value and assign back to it's param name."""

        # convert names back to snake_case
        params = {
            CaseUtil.pascal_to_snake_case(param_name): param_value
            for param_name, param_value in method_params.items()
        }

        # deserialize each param value
        for param_name, param_values in params.items():
            if not isinstance(param_values, dict):
                continue

            prepared_serialized_record = data_serializer.apply_ui_conversion(param_values)
            type_instance = data_serializer.deserialize_data(prepared_serialized_record)

            # assign deserialized value instead of dict
            params[param_name] = type_instance

        return params
