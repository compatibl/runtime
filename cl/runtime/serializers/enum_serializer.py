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
from enum import Enum
from typing import Any
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.for_dataclasses.data import Data
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.enum_format import EnumFormat
from cl.runtime.serializers.none_format import NoneFormat


@dataclass(slots=True, kw_only=True)
class EnumSerializer(Data):
    """Helper class for serialization and deserialization of enum types."""

    none_format: NoneFormat = required()
    """Serialization format for None."""

    enum_format: EnumFormat = required()
    """Serialization format for enums that are not None."""

    def serialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Serialize an enum to a string or another primitive type (return None if value is None)."""
        if data is None:
            if type_hint is not None and not type_hint.optional:
                raise RuntimeError(f"Enum {type_hint.schema_type_name} value is None but marked as required.")
            elif (value_format := self.none_format) == NoneFormat.PASSTHROUGH:
                return data
            else:
                raise ErrorUtil.enum_value_error(value_format, NoneFormat)
        elif isinstance(data, Enum):
            # Check that schema type matches if specified
            if type_hint is not None and type_hint.schema_type_name != (data_type_name := TypeUtil.name(data)):
                raise RuntimeError(
                    f"Enum value type {data_type_name} does not match the schema type {type_hint.schema_type_name}."
                )
            # Serialize according to settings
            if (value_format := self.enum_format) == EnumFormat.PASSTHROUGH:
                # Pass through the enum instance without changes
                return data
            elif value_format == EnumFormat.DEFAULT:
                # Serialize as name without type in PascalCase
                return CaseUtil.upper_to_pascal_case(data.name) if data is not None else None
            else:
                raise ErrorUtil.enum_value_error(value_format, EnumFormat)
        else:
            value_type_name = TypeUtil.name(type(data))
            raise RuntimeError(f"Type {value_type_name} provided to {self.__class__.__name__} is not an enum type.")

    def deserialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Deserialize a string or another primitive type to the specified enum type (return None if value is None)."""
        if type_hint is None:
            raise RuntimeError(f"Type hint is required for enum deserialization.")
        elif type_hint.schema_class is None:
            raise RuntimeError(f"Type hint must specify the class for enum deserialization.")
        elif data in [None, "", "null"]:
            if not type_hint.optional:
                raise RuntimeError(f"Enum {type_hint.schema_type_name} value is None but marked as required.")
            if (value_format := self.none_format) == NoneFormat.PASSTHROUGH:
                return data
            else:
                raise ErrorUtil.enum_value_error(value_format, NoneFormat)
        elif issubclass(enum_type := type_hint.schema_class, Enum):
            if (value_format := self.enum_format) == EnumFormat.PASSTHROUGH:
                # Pass through the enum instance without changes
                return data
            elif value_format == EnumFormat.DEFAULT:
                try:
                    # Serialized value is name without type in PascalCase, convert to UPPER_CASE
                    return enum_type[CaseUtil.pascal_to_upper_case(data)]
                except KeyError:
                    enum_type_name = TypeUtil.name(enum_type)
                    raise RuntimeError(f"Enum type {enum_type_name} does not include the item {data}.")
            else:
                raise ErrorUtil.enum_value_error(value_format, EnumFormat)
        else:
            schema_type_name = TypeUtil.name(enum_type)
            raise RuntimeError(
                f"Schema type {schema_type_name} provided to {self.__class__.__name__} is not an enum type."
            )
