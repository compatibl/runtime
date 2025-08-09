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
from typing import cast
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.protocols import TEnum
from cl.runtime.records.protocols import is_primitive
from cl.runtime.records.protocols import is_sequence
from cl.runtime.records.type_util import TypeUtil


class SettingsUtil:
    """Helper methods for Dynaconf settings."""

    @classmethod
    def to_enum(
        cls,
        value: Any,
        *,
        enum_type: type[TEnum],
        field_name: str | None = None,
        settings_type: type | None = None,
    ) -> TEnum:
        """Convert Dynaconf setting or env var to an enum, error if not specified."""
        if value:
            return cast(
                TEnum,
                cls.to_enum_or_none(
                    value,
                    enum_type=enum_type,
                    field_name=field_name,
                    settings_type=settings_type,
                ),
            )
        else:
            raise RuntimeError(f"Required {cls._what(field_name, settings_type)} is empty.")

    @classmethod
    def to_enum_or_none(
        cls,
        value: Any,
        *,
        enum_type: type[TEnum],
        field_name: str | None = None,
        settings_type: type | None = None,
    ) -> TEnum | None:
        """Convert Dynaconf setting or env var to an enum, None if not specified."""

        # Pass through None
        if not value:
            return None

        # Accept various input formats
        if CaseUtil.is_upper_case(value):
            upper_case_value = value
        elif CaseUtil.is_pascal_case(value):
            upper_case_value = CaseUtil.pascal_to_upper_case(value)
        elif CaseUtil.is_snake_case(value):
            upper_case_value = CaseUtil.snake_to_upper_case(value)
        else:
            raise RuntimeError(
                f"Value '{value}' for {cls._what(field_name, settings_type)}\n"
                f"must be UPPER_CASE, PascalCase, or snake_case."
            )

        # Check if the converted value is in the enum
        if upper_case_value in enum_type.__members__:
            return enum_type[upper_case_value]
        else:
            valid_values = "\n".join(CaseUtil.upper_to_pascal_case(item) for item in enum_type.__members__.keys())
            raise RuntimeError(
                f"Value '{value}' for {cls._what(field_name, settings_type)} does not match\n"
                f"any of the {TypeUtil.name(enum_type)} items. The list of accepted values is below.\n"
                f"The format can be UPPER_CASE, PascalCase, or snake_case.\n\n{valid_values}\n"
            )

    @classmethod
    def to_str_tuple(
        cls,
        value: Any,
        *,
        field_name: str | None = None,
        settings_type: type | None = None,
    ) -> tuple[str, ...]:
        """Convert Dynaconf setting or env var to a string tuple, error if not specified."""
        if value:
            return cast(
                tuple[str, ...],
                cls.to_str_tuple_or_none(
                    value,
                    field_name=field_name,
                    settings_type=settings_type,
                ),
            )
        else:
            raise RuntimeError(f"Required {cls._what(field_name, settings_type)} is empty.")

    @classmethod
    def to_str_tuple_or_none(
        cls,
        value: Any,
        *,
        field_name: str | None = None,
        settings_type: type | None = None,
    ) -> tuple[str, ...] | None:
        """Convert Dynaconf setting or env var to a string tuple, None if not specified."""
        if not value:
            return None
        elif is_sequence(value):
            # Already a sequence, convert to string and strip whitespace for each element
            return tuple(str(token).strip() for token in value)
        elif is_primitive(value):
            # Convert to string
            value = str(value)
            if value.startswith("[") and value.endswith("]"):
                # Strip leading and trailing square brackets if present
                value = value[1:-1]
            if "," in value:
                # Comma-separated string format with no quotes, for example a,b
                return tuple(token.strip() for token in value.split(","))
            else:
                # Single string value
                return (value,)
        else:
            raise RuntimeError(
                f"Cannot convert {cls._what(field_name, settings_type)} of type {TypeUtil.name(value)}\n"
                f"with value {value} to a string or a sequence of comma-delimited strings."
            )

    @classmethod
    def parse_comma_delimited_string(cls, value: str) -> tuple[str, ...]:
        # Remove square brackets if present
        value = value.strip().strip("[]")
        # Split by commas and strip whitespace from each value
        return tuple(item.strip() for item in value.split(",") if item.strip())

    @classmethod
    def _what(cls, field_name: str | None, settings_type: type | None) -> str:
        """Return a string describing the settings and its class."""
        field_name = f"setting '{field_name}'" if field_name else "a setting"
        settings_type_name = TypeUtil.name(settings_type) or "a settings class"
        return f"{field_name} in {settings_type_name}"
