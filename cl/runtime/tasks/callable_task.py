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
from cl.runtime.records.dataclasses_extensions import field
from cl.runtime.records.dataclasses_extensions import missing
from cl.runtime.serialization.ui_dict_serializer import UiDictSerializer
from cl.runtime.tasks.task import Task

data_serializer = UiDictSerializer()


@dataclass(slots=True, kw_only=True)
class MethodTask(Task, ABC):
    """Base class for tasks that invoke callables (class methods, functions, etc.)."""

    method_name: str = missing()
    """The name of @staticmethod in snake_case or PascalCase format."""

    method_params: dict[str, str | dict] | None = field(default_factory=dict)
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

    def deserialized_method_params(self) -> dict:
        """For every method's param - deserialize its value and assign back to it's param name."""

        # Convert names back to snake_case
        params = {
            CaseUtil.pascal_to_snake_case(param_name): param_value
            for param_name, param_value in self.method_params.items()
        }

        # Deserialize each param value
        for param_name, param_values in params.items():
            if not isinstance(param_values, dict):
                continue

            prepared_serialized_record = data_serializer.apply_ui_conversion(param_values)
            type_instance = data_serializer.deserialize_data(prepared_serialized_record)

            # Assign deserialized value instead of dict
            params[param_name] = type_instance

        return params
