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


from typing import Any, cast

from jinja2.utils import F
from cl.runtime.records.protocols import is_primitive, is_sequence
from cl.runtime.serializers.bootstrap_serializer import BootstrapSerializer
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers


class SettingsUtil:
    """Helper methods for Dynaconf settings."""

    @classmethod
    def to_str_tuple(
        cls,
        value: Any,
        *,
        field_name: str | None = None,
        type_name: str | None = None,
    ) -> tuple[str, ...]:
        if value:
            return cast(tuple[str, ...], cls.to_str_tuple_or_none(value, field_name=field_name, type_name=type_name))
        else:     
            raise RuntimeError(f"Required {cls._what(field_name, type_name)} is empty.")

    @classmethod
    def to_str_tuple_or_none(
        cls,
        value: Any,
        *,
        field_name: str | None = None,
        type_name: str | None = None,
    ) -> tuple[str, ...] | None:
        """Convert a setting to string tuple."""
        if not value:
            return None
        elif is_sequence(value):
            # Already a sequence, strip whitespace from each element
            return tuple(str(token).strip() for token in value)
        elif is_primitive(value):
            value = BootstrapSerializers.DEFAULT.serialize(value).strip()
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
            raise RuntimeError(f"Cannot convert {cls._what(field_name, type_name)} with value {value} to a sequence of strings.")


    @classmethod
    def _what(cls, field_name: str | None, type_name: str | None) -> str:
        """Return a string describing the settings and its class."""
        field_name = f"setting '{field_name}'" if field_name else "a setting"
        type_name = type_name or "a settings class"
        return f"{field_name} in {type_name}"
