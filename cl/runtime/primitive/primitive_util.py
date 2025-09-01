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
from cl.runtime.primitive.float_util import FloatUtil
from cl.runtime.primitive.limits import check_int_32
from cl.runtime.primitive.limits import check_int_54
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.builder_util import BuilderUtil
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES, is_primitive_type
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_hint import TypeHint

class PrimitiveUtil(BuilderUtil):
    """Helper methods for implementing the builder pattern with primitive fields."""

    @classmethod
    def build_(
        cls,
        data: Any,
        type_hint: TypeHint | None = None,
        *,
        outer_type_name: str | None = None,
        field_name: str | None = None,
    ) -> Any:

        # Handle None or empty first
        if data is None:
            if type_hint.optional:
                # Optional and has the value of None, return None
                return None
            else:
                # Required and has the value of None, raise an error
                location_str = cls._get_location_str(
                    typename(type(data)), type_hint, outer_type_name=outer_type_name, field_name=field_name
                )
                raise RuntimeError(f"Required field is not specified.{location_str}")

        # To allow ABCMeta and other metaclasses derived from type to pass the check
        data_class_name = "type" if isinstance(data, type) else typename(type(data))

        # Ensure there is no remaining component (type hint is not a sequence or mapping)
        if type_hint is not None and type_hint.remaining:
            raise RuntimeError(
                f"Data is an instance of a primitive class {data_class_name} which is\n"
                f"incompatible with a composite type hint:\n"
                f"{type_hint.to_str()}."
            )

        # Set schema_type_name based on type hint or data if not provided
        if type_hint is not None:
            schema_type_name = typename(type_hint.schema_type)
        else:
            schema_type_name = data_class_name

        # Validate that data type is compatible with schema type, allowing
        # mixing of int and float subject to subsequent validation of data value
        if (
                data_class_name != schema_type_name and
                not (data_class_name == "int" and schema_type_name == "float") and
                not (data_class_name == "float" and schema_type_name == "int")
        ):
            location_str = cls._get_location_str(
                typename(type(data)), type_hint, outer_type_name=outer_type_name, field_name=field_name
            )
            raise RuntimeError(
                f"Data type '{data_class_name}' cannot be stored in a field declared as '{schema_type_name}'."
                f"{location_str}"
            )

        # Validate that subtype is compatible with schema_type_name
        subtype = type_hint.subtype if type_hint is not None else None
        if (
            (schema_type_name == "int" and subtype not in (None, "long")) or
            (schema_type_name == "str" and subtype not in (None, "timestamp"))
        ):
            raise RuntimeError(f"Subtype '{subtype}' cannot be stored in class '{schema_type_name}'.")

        # Validate based schema_type_name, taking into account subtype
        if schema_type_name == "str":
            if subtype is None:
                # No further checks are required
                return data
            elif subtype == "timestamp":
                # Perform fast check for valid format
                assert Timestamp.guard_valid(data, fast=True, value_name=field_name, data_type=outer_type_name)
                return data
            else:
                location_str = cls._get_location_str(
                    typename(type(data)), type_hint, outer_type_name=outer_type_name, field_name=field_name
                )
                raise RuntimeError(f"Subtype {subtype} is not valid for data type {data_class_name}.{location_str}")
        elif schema_type_name == "int":
            # Perform range check based on subtype
            if subtype is None:
                # Check that the value is in 32-bit signed integer range
                # Check that it is within roundoff tolerance of an int if value is float, pass through if int
                return FloatUtil.to_int(data)
            elif subtype == "long":
                # Check that the value is in 54-bit signed integer range
                # Check that it is within roundoff tolerance of an int if value is float, pass through if int
                return FloatUtil.to_long(data)
            else:
                location_str = cls._get_location_str(
                    typename(type(data)), type_hint, outer_type_name=outer_type_name, field_name=field_name
                )
                raise RuntimeError(f"Subtype {subtype} is not valid for data type {data_class_name}.{location_str}")
        elif schema_type_name == "float":
            # Convert to float in case the argument is int
            return float(data)
        elif schema_type_name == "type":
            # Validate the type is known
            assert TypeCache.guard_known_type(data)
            return data
        elif schema_type_name in PRIMITIVE_CLASS_NAMES:
            # Pass through other types
            # TODO: !!! Add validation of datetime and other types, including for whole milliseconds
            return data
        else:
            primitive_class_names_str = "\n".join(PRIMITIVE_CLASS_NAMES)
            raise RuntimeError(
                f"Type {data_class_name} is not a valid value type for a primitive field:\n"
                f"{primitive_class_names_str}\n"
            )
