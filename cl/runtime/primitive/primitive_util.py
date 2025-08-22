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

from typing import Any

from cl.runtime.primitive.limits import check_int_32, check_int_54
from cl.runtime.records.protocols import PRIMITIVE_TYPE_NAMES
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_hint import TypeHint


class PrimitiveUtil:
    """Helper methods for primitive types."""

    @classmethod
    def normalize(cls, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Validate primitive data against the schema and return normalized value if necessary.."""

        # Get type name of data, which may be a type
        data_class_name = "type" if isinstance(data, type) else typename(data)

        # Get parameters from the type chain, considering the possibility that it may be None
        schema_type_name = type_hint.schema_type_name if type_hint is not None else None
        is_optional = type_hint.optional if type_hint is not None else None

        # Validate that schema_type_name is compatible with value_class_name if specified
        # Because the value of None is passed through, value_class_name NoneType is compatible with any schema_type_name
        if schema_type_name is not None and data_class_name != "NoneType" and schema_type_name != data_class_name:
            if schema_type_name == "long":
                if data_class_name != "int":
                    raise RuntimeError(
                        f"Type {schema_type_name} can only be stored using int class, not {data_class_name} class."
                    )
            elif schema_type_name == "timestamp":
                if data_class_name != "UUID":
                    raise RuntimeError(
                        f"Type {schema_type_name} can only be stored using UUID class, not {data_class_name} class."
                    )
            elif data is not None and data_class_name != schema_type_name:
                raise RuntimeError(f"Type {schema_type_name} cannot be stored as {data_class_name} class.")

        # Normalize based on value_class_name, using schema_type_name to distinguish between types that share the same class
        if data is None:
            if is_optional:
                return None
            else:
                raise RuntimeError(
                    f"A field of type {typename(schema_type_name)} is None but declared as required.")
        elif data_class_name == "str":
            return data if data else None
        elif data_class_name == "float":
            return data
        elif data_class_name == "bool":
            return data
        elif data_class_name == "int":
            if schema_type_name is not None and schema_type_name == "int":
                # Check that the value is in 32-bit signed integer range
                # if schema_type_name is specified and is int rather than long
                check_int_32(data)
                return data
            elif schema_type_name is not None and schema_type_name == "long":
                # Check that the value is in 54-bit signed integer range
                # if schema_type_name is specified and is long
                check_int_54(data)
                return data
            else:
                # Otherwise do not perform range checks and use the convention for long
                # TODO: Use conventions depending on value instead?
                return data
        elif data_class_name == "date":
            return data
        elif data_class_name == "time":
            return data
        elif data_class_name == "datetime":
            return data
        elif data_class_name == "UUID":
            if data.version != 7 or (schema_type_name is not None and schema_type_name == "UUID"):
                return data
            else:
                # Under else, value.version == 7 and schema_type_name != "UUID"
                if schema_type_name is not None and schema_type_name != "timestamp":
                    raise RuntimeError("For UUID version 7, only UUID or timestamp types are valid.")
                return data
        elif data_class_name == "bytes":
            return data
        elif data_class_name == "type":
            assert TypeCache.guard_known_type(data)
            return data
        else:
            primitive_types_str = "\n".join(PRIMITIVE_TYPE_NAMES)
            raise RuntimeError(
                f"Type {data_class_name} is not one of the supported primitive types:\n{primitive_types_str}\n")
