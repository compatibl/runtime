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
from cl.runtime.records.protocols import is_primitive_type
from cl.runtime.records.protocols import is_sequence_type
from cl.runtime.records.typename import typename
from cl.runtime.records.typename import typenameof
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.slots_util import SlotsUtil
from cl.runtime.settings.settings import Settings

_SERIALIZER = BootstrapSerializers.DEFAULT


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

        # Pass through an instance of the specified enum type
        if isinstance(value, enum_type):
            return value

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
                f"any of the {typename(enum_type)} items. The list of accepted values is below.\n"
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
        elif is_sequence_type(type(value)):
            # Already a sequence, convert to string and strip whitespace for each element
            return tuple(str(token).strip() for token in value)
        elif is_primitive_type(type(value)):
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
                f"Cannot convert {cls._what(field_name, settings_type)} of type {typename(type(value))}\n"
                f"with value {value} to a string or a sequence of comma-delimited strings."
            )

    @classmethod
    def to_object(
        cls,
        *,
        settings: Settings,
        prefix: str,
    ) -> Any:
        """Create a new object from a group of settings fields with the same prefix, error if none are set."""
        result = cls.to_object_or_none(
            settings=settings,
            prefix=prefix,
        )
        if result is None:
            raise RuntimeError(f"Required field(s) with prefix '{prefix}' are not set in {typenameof(settings)}.")
        return result

    @classmethod
    def to_object_or_none(
        cls,
        *,
        settings: Settings,
        prefix: str,
    ) -> Any:
        """Create a new object from a group of settings fields with the same prefix, return None if none are set."""

        # Add the trailing underscore if not included in argument
        prefix = prefix if prefix.endswith("_") else prefix + "_"

        # Get a dict with all fields that have the prefix
        field_names = SlotsUtil.get_field_names(type(settings))
        result_dict = {x: getattr(settings, x, None) for x in field_names if x.startswith(prefix)}

        # Remove all values that are None
        result_dict = {k: v for k, v in result_dict.items() if v is not None}

        # Deserialize and build if not empty
        if result_dict:
            if (result_type_name := result_dict.pop(prefix + "type_name", None)) is not None:
                # Rename the key for type if present
                result_dict["_type"] = result_type_name
            else:
                # Error message otherwise
                raise RuntimeError(
                    f"Attribute '{prefix}type_name' is required in {typenameof(settings)}\n"
                    f"to create an object with prefix '{prefix}'."
                )

            # Deserialize based on _type
            result = DataSerializers.DEFAULT.deserialize(result_dict).build()
            return result
        else:
            # None of the fields with the specified prefix are set, return None
            return None

    @classmethod
    def parse_comma_delimited_string(cls, value: str) -> tuple[str, ...]:  # TODO: Check if this is used anywhere
        """Parse a comma-delimited string into a tuple of strings."""
        # Remove square brackets if present
        value = value.strip().strip("[]")
        # Split by commas and strip whitespace from each value
        return tuple(item.strip() for item in value.split(",") if item.strip())

    @classmethod
    def _what(cls, field_name: str | None, settings_type: type | None) -> str:
        """Return a string describing the settings and its class."""
        field_name = f"setting '{field_name}'" if field_name else "a setting"
        settings_type_name = typename(settings_type) or "a settings class"
        return f"{field_name} in {settings_type_name}"
