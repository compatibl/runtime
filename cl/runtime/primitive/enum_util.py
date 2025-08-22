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

from enum import Enum
from typing import Any

from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.string_util import StringUtil
from cl.runtime.records.protocols import TEnum
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_hint import TypeHint


class EnumUtil:
    """Helper methods for enums."""

    @classmethod
    def to_str(cls, value: Enum | None) -> str:
        """Convert Enum instance to PascalCase string."""
        return CaseUtil.upper_to_pascal_case(value.name)

    @classmethod
    def from_str(
        cls,
        enum_type: type[TEnum],
        value: str | None,
        *,
        field_name: str | None = None,
        class_name: str | None = None,
    ) -> TEnum:
        """Convert PascalCase string to Enum instance."""
        # Convert from PascalCase to UPPER_CASE for matching but not error reporting
        if CaseUtil.is_pascal_case(value):
            uppercase_value = CaseUtil.pascal_to_upper_case(value)
        else:
            description = cls.get_description(enum_type, value, field_name=field_name, class_name=class_name)
            raise UserError(f"The {description} is UPPER_CASE, use PascalCase instead.")

        try:
            # Use item name, not value which may be numerical for IntEnum
            return enum_type[uppercase_value]
        except KeyError:
            description = cls.get_description(enum_type, value, field_name=field_name, class_name=class_name)
            valid_values = "".join([f"  - {CaseUtil.upper_to_pascal_case(e.name)}\n" for e in enum_type])
            raise UserError(f"Invalid {description}. Valid choices:\n{valid_values}")

    @classmethod
    def get_description(
        cls,
        enum_type: type[TEnum],
        value: str | None,
        *,
        field_name: str | None = None,
        class_name: str | None = None,
    ) -> str:
        description = f"value '{value}' for "
        if not StringUtil.is_empty(field_name):
            if CaseUtil.is_pascal_case(field_name):
                field_name = CaseUtil.snake_to_pascal_case(field_name)
            description = description + f"field '{field_name}'"
        else:
            description = description + f"type {enum_type.__name__}"
        if not StringUtil.is_empty(class_name):
            description = description + f" in record type {class_name}"
        return description

    @classmethod
    def normalize(cls, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Normalize an enum based on type hint (return None if value is None)."""
        if data is None:
            if type_hint is not None and not type_hint.optional:
                raise RuntimeError(f"Enum {type_hint.schema_type_name} value is None but marked as required.")
            return data
        elif isinstance(data, Enum):
            # Check that schema type matches if specified
            if type_hint is not None and type_hint.schema_type_name != (data_type_name := typename(data)):
                raise RuntimeError(
                    f"Enum value type {data_type_name} does not match the schema type {type_hint.schema_type_name}."
                )
            return data
        else:
            value_type_name = typename(type(data))
            raise RuntimeError(f"Type {value_type_name} provided to {self.__class__.__name__} is not an enum type.")
