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
from dataclasses import dataclass
from enum import Enum
from enum import IntEnum
from uuid import UUID
from cl.runtime.primitive.bool_format_enum import BoolFormatEnum
from cl.runtime.primitive.bool_util import BoolUtil
from cl.runtime.primitive.bytes_format_enum import BytesFormatEnum
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.date_format_enum import DateFormatEnum
from cl.runtime.primitive.date_util import DateUtil
from cl.runtime.primitive.datetime_format_enum import DatetimeFormatEnum
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.float_format_enum import FloatFormatEnum
from cl.runtime.primitive.float_util import FloatUtil
from cl.runtime.primitive.int_format_enum import IntFormatEnum
from cl.runtime.primitive.int_util import IntUtil
from cl.runtime.primitive.long_format_enum import LongFormatEnum
from cl.runtime.primitive.long_util import LongUtil
from cl.runtime.primitive.none_format_enum import NoneFormatEnum
from cl.runtime.primitive.string_format_enum import StringFormatEnum
from cl.runtime.primitive.time_format_enum import TimeFormatEnum
from cl.runtime.primitive.time_util import TimeUtil
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.primitive.timestamp_format_enum import TimestampFormatEnum
from cl.runtime.primitive.uuid_format_enum import UuidFormatEnum
from cl.runtime.primitive.uuid_util import UuidUtil
from cl.runtime.records.for_dataclasses.freezable import Freezable
from cl.runtime.records.protocols import TPrimitive
from cl.runtime.records.type_util import TypeUtil


@dataclass(slots=True, kw_only=True)
class PrimitiveSerializer(Freezable):
    """Helper class for serialization and deserialization of primitive types."""

    none_format: NoneFormatEnum | None = None
    """Serialization format for None (pass through without conversion if not set)."""

    string_format: StringFormatEnum | None = None
    """Serialization format for str (pass through without conversion if not set)."""

    float_format: FloatFormatEnum | None = None
    """Serialization format for float (pass through without conversion if not set)."""

    bool_format: BoolFormatEnum | None = None
    """Serialization format for bool (pass through without conversion if not set)."""

    int_format: IntFormatEnum | None = None
    """Serialization format for int (pass through without conversion if not set)."""

    long_format: LongFormatEnum | None = None
    """Serialization format for long (pass through without conversion if not set)."""

    date_format: DateFormatEnum | None = None
    """Serialization format for dt.date (pass through without conversion if not set)."""

    datetime_format: DatetimeFormatEnum | None = None
    """Serialization format for dt.datetime (pass through without conversion if not set)."""

    time_format: TimeFormatEnum | None = None
    """Serialization format for dt.time (pass through without conversion if not set)."""

    uuid_format: UuidFormatEnum | None = None
    """Serialization format for UUID other than UUIDv7 (pass through without conversion if not set)."""

    timestamp_format: TimestampFormatEnum | None = None
    """Serialization format for UUIDv7 unique timestamp (pass through without conversion if not set)."""

    bytes_format: BytesFormatEnum | None = None
    """Serialization format for bytes (pass through without conversion if not set)."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if self.long_format is None:
            # Set long format based on int format if not set
            match self.int_format:
                case None:
                    self.long_format = None
                case IntFormatEnum.DEFAULT:
                    self.long_format = LongFormatEnum.DEFAULT
                case _:
                    raise RuntimeError(f"Unknown value {self.int_format} of int_format.")

        if self.timestamp_format is None:
            # Set timestamp format based on UUID format if not set
            match self.uuid_format:
                case None:
                    self.timestamp_format = None
                case UuidFormatEnum.DEFAULT:
                    self.timestamp_format = TimestampFormatEnum.DEFAULT
                case _:
                    raise RuntimeError(f"Unknown value {self.uuid_format} of uuid_format.")

    def serialize(self, value: TPrimitive | None, type_name: str | None = None) -> TPrimitive | None:
        """
        Serialize a primitive type to a string or another primitive type.

        Returns:
            A string or another serialization output such as int or None

        Args:
            value: An instance of primitive class from PRIMITIVE_CLASS_NAMES
            type_name: Optional type name to use for validation and to identify a type that shares
                       the same class with another type (e.g. long and int types share the int class)
        """
        # Match by class name rather than class type because different import packages may be used for some of the
        # primitive types such as UUID throughout the code, so class types may not always match but class names will
        class_name = value.__class__.__name__

        # Validate that type_name is compatible with class_name if specified
        # Because the value of None is passed through, class_name NoneType is compatible with any type_name
        if type_name is not None and class_name != "NoneType" and type_name != class_name:
            if type_name == "long" and class_name != "int":
                raise RuntimeError(f"Type {type_name} can only be stored using int class, not {class_name} class.")
            elif type_name == "timestamp" and class_name != "UUID":
                raise RuntimeError(f"Type {type_name} can only be stored using UUID class, not {class_name} class.")
            elif class_name != type_name:
                raise RuntimeError(f"Type {type_name} cannot be stored as {class_name} class.")

        # Serialize based on class_name, using type_name to distinguish between types that share the same class
        if value is None:
            return None
        elif class_name == "str":
            # Return None for an empty string
            return value if value else None
        elif class_name == "float":
            if (value_format := self.float_format) is None:
                return value
            elif value_format == FloatFormatEnum.DEFAULT:
                return FloatUtil.format(value)
            else:
                raise self._enum_error(value_format)
        elif class_name == "bool":
            if (value_format := self.bool_format) is None:
                return value
            elif value_format == BoolFormatEnum.DEFAULT:
                return BoolUtil.format(value)
            else:
                raise self._enum_error(value_format)
        elif class_name == "int":
            if type_name is not None and type_name == "int":
                # Use methods that check that the value is in 32-bit signed integer range
                # if type_name is specified and is int rather than long
                if (value_format := self.int_format) is None:
                    IntUtil.check_range(value)
                    return value
                elif value_format == IntFormatEnum.DEFAULT:
                    return IntUtil.to_str(value)
                else:
                    raise self._enum_error(value_format)
            else:
                # Otherwise do not perform range checks
                if (value_format := self.long_format) is None:
                    return value
                elif value_format == LongFormatEnum.DEFAULT:
                    return LongUtil.to_str(value)
                else:
                    raise self._enum_error(value_format)
        elif class_name == "date":
            if (value_format := self.date_format) is None:
                return value
            elif value_format == DateFormatEnum.DEFAULT:
                return DateUtil.to_str(value)
            else:
                raise self._enum_error(value_format)
        elif class_name == "time":
            if (value_format := self.time_format) is None:
                return value
            elif value_format == TimeFormatEnum.DEFAULT:
                return TimeUtil.to_str(value)
            else:
                raise self._enum_error(value_format)
        elif class_name == "datetime":
            if (value_format := self.datetime_format) is None:
                return value
            elif value_format == DatetimeFormatEnum.DEFAULT:
                return DatetimeUtil.to_str(value)
            else:
                raise self._enum_error(value_format)
        elif class_name == "UUID":
            if value.version != 7 or (type_name is not None and type_name == "UUID"):
                if (value_format := self.uuid_format) is None:
                    return value
                elif value_format == UuidFormatEnum.DEFAULT:
                    # Use the standard delimited UUID format
                    return UuidUtil.to_str(value)
                else:
                    raise self._enum_error(value_format)
            else:
                # Under else, value.version == 7 and type_name != "UUID"
                if type_name is not None and type_name != "timestamp":
                    raise RuntimeError("For UUID version 7, only UUID or timestamp types are valid.")

                if (value_format := self.timestamp_format) is None:
                    return value
                elif value_format == TimestampFormatEnum.DEFAULT:
                    # Use timestamp-hex UUIDv7 format
                    return Timestamp.from_uuid7(value)
                else:
                    raise self._enum_error(value_format)
        elif class_name == "bytes":
            if (value_format := self.bytes_format) is None:
                return value
            elif value_format == BytesFormatEnum.DEFAULT:
                # Base64 encoding for bytes with MIME line wrap convention at 76 characters, remove trailing EOL
                return base64.encodebytes(value).decode("utf-8").rstrip("\n")  # TODO: Create BytesUtil
            else:
                raise self._enum_error(value_format)
        else:
            raise RuntimeError(f"Class {class_name} cannot be serialized using {type(self).__name__}.")

    def deserialize(self, value: TPrimitive | None, type_name: str) -> TPrimitive | None:
        """
        Deserialize a string or another primitive value such as int or None to an instance of type_name.

        Returns:
            An instance of type_name, which must be one of PRIMITIVE_CLASS_NAMES, including None

        Args:
            value: A string or another serialization output such as int or None
            type_name: Type name is required to avoid guessing the type from serialized value  and to identify a type
                       that uses the same class as another type (e.g., long and int types share the int class)
        """
        if type_name == "NoneType":
            if value in [None, "", "null"]:
                # Treat an empty string and "null" as None
                return None
            else:
                raise self._deserialization_error(value, type_name, self.none_format)
        elif type_name == "str":
            if value in [None, "", "null"]:
                # Treat an empty string and "null" as None
                return None
            else:
                if isinstance(value, str):
                    # Pass through string
                    return value
                else:
                    raise self._deserialization_error(value, type_name, self.string_format)
        elif type_name == "float":
            if (value_format := self.float_format) is None:
                if value is None or isinstance(value, float):
                    # Pass through None and float
                    return value
                elif isinstance(value, int):
                    # Convert int to float
                    return float(value)
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            elif value_format == FloatFormatEnum.DEFAULT:
                if value in [None, "", "null"]:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(value, str):
                    # Deserialize from string
                    return float(value)  # TODO: !!! Use FloatUtil
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            else:
                raise self._enum_error(value_format)
        elif type_name == "bool":
            if (value_format := self.bool_format) is None:
                if value is None or isinstance(value, bool):
                    # Pass through None and bool
                    return value
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            elif value_format == BoolFormatEnum.DEFAULT:
                if value in [None, "", "null"]:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(value, str):
                    # Deserialize from string
                    return BoolUtil.parse(value)
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            else:
                raise self._enum_error(value_format)
        elif type_name == "int":
            if (value_format := self.int_format) is None:
                if value is None:
                    # Pass through None
                    return value
                elif isinstance(value, int):
                    # Passthrough int after checking that value is within 32-bit signed integer range
                    IntUtil.check_range(value)
                    return value
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            elif value_format == IntFormatEnum.DEFAULT:
                if value in [None, "", "null"]:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(value, str):
                    # Checks that value is within 32-bit signed integer range
                    return IntUtil.from_str(value)
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            else:
                raise self._enum_error(value_format)
        elif type_name == "long":
            if (value_format := self.long_format) is None:
                if value is None or isinstance(value, int):
                    # Pass through None and int
                    return value
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            elif value_format == LongFormatEnum.DEFAULT:
                if value in [None, "", "null"]:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(value, str):
                    return LongUtil.from_str(value)
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            else:
                raise self._enum_error(value_format)
        elif type_name == "date":
            if (value_format := self.date_format) is None:
                if value is None or isinstance(value, dt.date):
                    # Pass through None and dt.date
                    return value
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            elif value_format == DateFormatEnum.DEFAULT:
                if value in [None, "", "null"]:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(value, str):
                    return DateUtil.from_str(value)
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            else:
                raise self._enum_error(value_format)
        elif type_name == "time":
            if (value_format := self.time_format) is None:
                if value is None or isinstance(value, dt.time):
                    # Pass through None and dt.time
                    return value
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            elif value_format == TimeFormatEnum.DEFAULT:
                if value in [None, "", "null"]:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(value, str):
                    return TimeUtil.from_str(value)
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            else:
                raise self._enum_error(value_format)
        elif type_name == "datetime":
            if (value_format := self.datetime_format) is None:
                if value is None or isinstance(value, dt.datetime):
                    # Pass through None and dt.datetime
                    return value
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            elif value_format == DatetimeFormatEnum.DEFAULT:
                if value in [None, "", "null"]:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(value, str):
                    return DatetimeUtil.from_str(value)
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            else:
                raise self._enum_error(value_format)
        elif type_name == "UUID":
            if (value_format := self.uuid_format) is None:
                if value is None or isinstance(value, UUID):
                    # Pass through None and UUID
                    return value
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            elif value_format == UuidFormatEnum.DEFAULT:
                if value in [None, "", "null"]:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(value, str):
                    # Accepts both standard format for any UUID version and timestamp-hex format for version 7
                    return UuidUtil.from_str(value)
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            else:
                raise self._enum_error(value_format)
        elif type_name == "timestamp":
            if (value_format := self.timestamp_format) is None:
                if value is None:
                    # Pass through None
                    return value
                elif isinstance(value, UUID):
                    # Pass through UUID after checking version
                    if value.version != 7:
                        raise RuntimeError("For timestamp type, only version 7 of UUID is valid.")
                    return value
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            elif value_format == TimestampFormatEnum.DEFAULT:
                if value in [None, "", "null"]:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(value, str):
                    # Accepts both standard format for any UUID version and timestamp-hex format for version 7
                    result = UuidUtil.from_str(value)
                    if result.version != 7:
                        raise RuntimeError("For timestamp type, only version 7 of UUID is valid.")
                    return result
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            else:
                raise self._enum_error(value_format)
        elif type_name == "bytes":
            if (value_format := self.bytes_format) is None:
                if value is None or isinstance(value, bytes):
                    # Pass through None and bytes
                    return value
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            elif value_format == BytesFormatEnum.DEFAULT:
                if value in [None, "", "null"]:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(value, str):
                    return base64.b64decode(value)  # TODO: Create BytesUtil
                else:
                    raise self._deserialization_error(value, type_name, value_format)
            else:
                raise self._enum_error(value_format)

    @classmethod
    def _enum_error(cls, value_format: Enum) -> Exception:
        """Error message on unknown format enum."""
        enum_class_name = value_format.__class__.__name__
        enum_value_str = CaseUtil.upper_to_pascal_case(value_format.name)
        return RuntimeError(f"{cls.__name___} does not support {enum_class_name} value of {enum_value_str}.")

    @classmethod
    def _deserialization_error(cls, value: TPrimitive | None, type_name: str, type_format: IntEnum) -> Exception:
        """Error message on deserialization failure."""
        value_type_name = TypeUtil.name(type(value))
        value_format_str = f"{type_format.__class__} set to {type_format.name}"
        value_str = f"\n{value}\n" if isinstance(value, str) and "\n" in value else value
        return RuntimeError(
            f"{cls.__name__} cannot deserialize to type {type_name} with {value_format_str}.\n"
            f"Input value type: {value_type_name}\n"
            f"Input value: {value_str}"
        )
