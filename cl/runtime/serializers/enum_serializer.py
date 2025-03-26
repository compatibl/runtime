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
from typing import Type
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.enum_format_enum import EnumFormatEnum
from cl.runtime.primitive.none_format_enum import NoneFormatEnum
from cl.runtime.records.for_dataclasses.data import Data
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import TPrimitive
from cl.runtime.records.type_util import TypeUtil


@dataclass(slots=True, kw_only=True)
class EnumSerializer(Data):
    """Helper class for serialization and deserialization of enum types."""

    none_format: NoneFormatEnum = required()
    """Serialization format for None."""

    enum_format: EnumFormatEnum = required()
    """Serialization format for enums that are not None."""

    def serialize(self, value: Enum | None, enum_type: Type | None = None) -> TPrimitive | None:
        """Serialize an enum to a string or another primitive type (return None if value is None)."""
        if value is None:
            if (value_format := self.none_format) == NoneFormatEnum.PASSTHROUGH:
                return value
            else:
                raise ErrorUtil.enum_value_error(value_format, NoneFormatEnum)
        elif isinstance(value, Enum):
            # Check that schema type matches if specified
            if enum_type is not None and type(value) is not enum_type:
                value_type_name = TypeUtil.name(type(value))
                schema_type_name = TypeUtil.name(enum_type)
                raise RuntimeError(
                    f"Type {value_type_name} of enum value does not match the type in schema {schema_type_name}"
                )
            # Serialize according to settings
            if (value_format := self.enum_format) == EnumFormatEnum.PASSTHROUGH:
                # Pass through the enum instance without changes
                return value
            elif value_format == EnumFormatEnum.DEFAULT:
                # Serialize as name without type in PascalCase
                return CaseUtil.upper_to_pascal_case(value.name) if value is not None else None
            else:
                raise ErrorUtil.enum_value_error(value_format, EnumFormatEnum)
        else:
            value_type_name = TypeUtil.name(type(value))
            raise RuntimeError(f"Type {value_type_name} provided to {self.__class__.__name__} is not an enum type.")

    def deserialize(self, value: TPrimitive | None, enum_type: Type) -> Enum | None:
        """Deserialize a string or another primitive type to the specified enum type (return None if value is None)."""
        if value is None:
            if (value_format := self.none_format) == NoneFormatEnum.PASSTHROUGH:
                return value
            else:
                raise ErrorUtil.enum_value_error(value_format, NoneFormatEnum)
        elif issubclass(enum_type, Enum):
            if (value_format := self.enum_format) == EnumFormatEnum.PASSTHROUGH:
                # Pass through the enum instance without changes
                return value
            elif value_format == EnumFormatEnum.DEFAULT:
                try:
                    # Serialized value is name without type in PascalCase, convert to UPPER_CASE
                    return enum_type[CaseUtil.pascal_to_upper_case(value)]
                except KeyError:
                    enum_type_name = TypeUtil.name(enum_type)
                    raise RuntimeError(f"Enum type {enum_type_name} does not include the item {value}.")
            else:
                raise ErrorUtil.enum_value_error(value_format, EnumFormatEnum)
        else:
            schema_type_name = TypeUtil.name(enum_type)
            raise RuntimeError(
                f"Schema type {schema_type_name} provided to {self.__class__.__name__} is not an enum type."
            )
