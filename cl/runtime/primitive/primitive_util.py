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

from typing import Any, Type
from typing import Tuple
from cl.runtime.records.type_util import TypeUtil


class PrimitiveUtil:
    """Helper methods for primitive types."""

    @classmethod
    def check_type(
        cls,
        instance_or_type: Any,
        schema_type_name: str,
        *,
        name: str | None = None,
    ) -> None:
        """
        Raises an error if the type of 'instance_or_type' is not 'schema_type', subclasses are not permitted.

        Args:
            instance_or_type: Actual object or type
            schema_type_name: Expected primitive type name, may not match class name (e.g., 'long' or 'timestamp')
            name: Lowercase name of parameter or field (optional)
        """
        # If not a type, assume it is an instance
        value_class_name = TypeUtil.name(instance_or_type)

        # Validate that schema_type_name is compatible with value_class_name if specified
        # Because the value of None is passed through, value_class_name NoneType is compatible with any schema_type_name
        if schema_type_name is not None and value_class_name != "NoneType" and schema_type_name != value_class_name:
            if schema_type_name == "long":
                if value_class_name != "int":
                    raise RuntimeError(
                        f"Type {schema_type_name} can only be stored using int class, not {value_class_name} class."
                    )
            elif schema_type_name == "timestamp":
                if value_class_name != "UUID":
                    raise RuntimeError(
                        f"Type {schema_type_name} can only be stored using UUID class, not {value_class_name} class."
                    )
            elif value_class_name != schema_type_name:
                raise RuntimeError(f"Type {schema_type_name} cannot be stored as {value_class_name} class.")
