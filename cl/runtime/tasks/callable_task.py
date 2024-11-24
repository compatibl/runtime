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
import base64
import re
from abc import ABC
from dataclasses import dataclass

from inflection import underscore

from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.serialization.dict_serializer import DictSerializer
from cl.runtime.serialization.info.method_info import MethodInfo
from cl.runtime.serialization.string_serializer import StringSerializer
from cl.runtime.tasks.task import Task

key_serializer = StringSerializer()
param_dict_serializer = DictSerializer()  # TODO: Support complex params


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
    def deserialize_method_params(_type: type, method_name: str, method_params: dict) -> dict:
        params = dict()
        if not method_params:
            return params

        # convert names back to snake_case
        params = {
            CaseUtil.pascal_to_snake_case(param_name): param_value
            for param_name, param_value in method_params.items()
        }

        # map param name to it's type
        method_info = MethodInfo(_type, method_name)
        param_types = {arg_info.name: arg_info for arg_info in method_info.arguments}

        # deserialize each param
        for param_name, param_values in params.items():
            if isinstance(param_values, dict):
                # decl = TypeDecl.for_type(param_types[param_name].type)
                param_values_normalized = dict()
                for arg_name, arg_value in param_values.items():
                    name = CaseUtil.pascal_to_snake_case(arg_name)
                    value = arg_value
                    if arg_name == "FileBytes":
                        value = base64.b64decode(value.encode())

                    param_values_normalized[name] = value

                params[param_name] = param_types[param_name].type(**param_values_normalized)
        return params
