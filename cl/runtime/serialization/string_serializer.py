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
import datetime as dt
from enum import Enum
from typing import Any
from typing import Generator
from typing import Tuple
from typing import Type
from typing import get_type_hints
from uuid import UUID
from cl.runtime.primitive.date_util import DateUtil
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.time_util import TimeUtil
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import TPrimitive
from cl.runtime.records.protocols import is_key

# TODO (Roman): remove dependency from dict_serializer
from cl.runtime.serialization.dict_serializer import _get_class_hierarchy_slots
from cl.runtime.serialization.dict_serializer import alias_dict
from cl.runtime.serialization.dict_serializer import get_type_dict

primitive_type_names = frozenset(
    {"NoneType", "str", "float", "int", "bool", "date", "time", "datetime", "bytes", "UUID"}
)
"""Detect primitive type by checking if class name is in this list."""


# TODO: Add checks for custom override of default serializer inside the class
class StringSerializer:
    """Serialize key to string, flattening hierarchical structure."""

    @classmethod
    def serialize_primitive(cls, value: TPrimitive) -> str | None:
        """Serialize primitive type to string."""
        if value is None:
            return None
        elif value.__class__.__name__ == "str":
            return value
        elif value.__class__.__name__ in ("date", "datetime", "time"):
            # Serialize date types to iso string
            if value.__class__.__name__ == "datetime":
                datetime_obj = DatetimeUtil.round(value)
                return DatetimeUtil.to_str(datetime_obj)
            elif value.__class__.__name__ == "date":
                return DateUtil.to_str(value)
            elif value.__class__.__name__ == "time":
                return TimeUtil.to_str(value)
        elif value.__class__.__name__ in ("UUID", "int", "float"):
            # Serialize UUID to string
            return str(value)
        elif value.__class__.__name__ == "bytes":
            # Decode bytes to base64 string
            return base64.b64encode(value).decode()
        elif value.__class__.__name__ == "bool":
            # Serialize bool to Y/N char
            return "Y" if value else "N"
        else:
            raise RuntimeError(f"Value of type {value.__class__} is not primitive.")

    @classmethod
    def deserialize_primitive(cls, str_value: str, type_: Type) -> TPrimitive:
        """Deserialize string to primitive type."""
        if str_value is None:
            return None
        elif type_.__name__ == "str":
            return str_value
        # TODO (Roman): Remove check for Any when no longer supported.
        elif type_ is None or type_.__name__ == "str" or type_ is Any:
            # Return unchanged if declared type is string
            return str_value
        elif type_.__name__ == "datetime":
            # Deserialize datetime from iso string
            datetime_value = DatetimeUtil.from_str(str_value)
            return DatetimeUtil.round(datetime_value.replace(tzinfo=dt.timezone.utc))
        elif type_.__name__ == "date":
            # Deserialize date from iso string
            return DateUtil.from_str(str_value)
        elif type_.__name__ == "time":
            # Deserialize time from iso string
            return TimeUtil.from_str(str_value)
        elif type_.__name__ == "bool":
            # Deserialize bool from string
            if (bool_value := True if str_value == "Y" else False if str_value == "N" else None) is not None:
                return bool_value
            else:
                raise RuntimeError(f"Serialized boolean field has value {str_value} but only Y/N and 1/0 are allowed.")
        elif type_.__name__ == "UUID":
            # Create UUID from string
            return UUID(str_value)
        elif type_.__name__ == "bytes":
            # Encode base64 string to bytes
            return base64.b64decode(str_value.encode())
        elif type_.__name__ == "int":
            # Support string value for declared as int
            return int(str_value)
        elif type_.__name__ == "float":
            # Support string value for declared as float
            return float(str_value)
        else:
            raise RuntimeError(f"Type '{type_}' is not primitive.")

    @classmethod
    def _serialize_key_token(cls, data) -> str:
        """Serialize key field to string token."""

        if data is None:
            # TODO (Roman): make different None and empty string
            return ""

        if isinstance(data, Enum):
            # Get enum short name and cache to type_dict
            short_name = alias_dict[type_] if (type_ := type(data)) in alias_dict else type_.__name__
            type_dict = get_type_dict()
            type_dict[short_name] = type_

            return f"{short_name}.{data.name}"
        else:
            return cls.serialize_primitive(data)

    @classmethod
    def _deserialize_key_token(cls, token: str, slot_type: Type):
        """Deserialize single key token in str format."""
        if issubclass(slot_type, Enum):
            enum_type, enum_value = token.split(".")
            type_dict = get_type_dict()
            deserialized_type = type_dict.get(enum_type, None)  # noqa
            if deserialized_type is None:
                raise RuntimeError(
                    f"Enum not found for name or alias '{enum_type}' during key token deserialization. "
                    f"Ensure all serialized enums are included in package import settings."
                )

            # Get enum value
            return deserialized_type[enum_value]  # noqa
        elif (primitive := cls.deserialize_primitive(token, slot_type)) is not None:
            return primitive
        else:
            raise RuntimeError(f"Unsupported key field type: {slot_type}.")

    @classmethod
    def _iter_key_slots(cls, key: KeyProtocol) -> Generator[Tuple[KeyProtocol, str, Type], None, None]:
        """
        Iterate over key slots including slots of embedded keys.
        If slot type is key - create embedded key object and yield its slots.
        """

        key_slots = _get_class_hierarchy_slots(key.__class__)
        key_hints = get_type_hints(key.__class__)

        for slot in key_slots:
            slot_type = key_hints.get(slot)

            if slot_type is not None and is_key(slot_type):
                # Create nested key object
                nested_key = slot_type()
                setattr(key, slot, nested_key)
                yield from cls._iter_key_slots(nested_key)
            else:
                yield key, slot, slot_type

    def serialize_key(self, data) -> str:
        """Serialize key to string, flattening for composite keys."""

        if not is_key(data):
            raise RuntimeError(f"Argument of serialize_key is not a key: {data}")

        key_slots = _get_class_hierarchy_slots(data.get_key_type())
        result = ";".join(
            (
                self._serialize_key_token(v)
                if (v := getattr(data, k)).__class__.__name__ in primitive_type_names or isinstance(v, Enum)
                else self.serialize_key(v)
            )
            for k in key_slots
        )

        return result

    def deserialize_key(self, key_as_str: str, key_type: Type[KeyProtocol]):
        """Deserialize ';' delimited key string."""

        key_tokens = key_as_str.split(";")
        key_obj = key_type()

        slots_iterator = iter(self._iter_key_slots(key_obj))
        for token in key_tokens:
            obj, slot, slot_type = next(slots_iterator)

            if (
                slot_type is not None
                and slot_type.__name__ not in primitive_type_names
                and not issubclass(slot_type, Enum)
            ):
                raise RuntimeError(
                    f"Unsupported key field type '{slot_type}' in class '{obj.__class__}' for field '{slot}'"
                )

            slot_value = self._deserialize_key_token(token, slot_type)
            setattr(obj, slot, slot_value)

        return key_obj
