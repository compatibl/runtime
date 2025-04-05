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
from enum import IntEnum
from typing import Sequence, Any, Tuple, Type
from uuid import UUID
from bson import Int64
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.bool_util import BoolUtil
from cl.runtime.primitive.date_util import DateUtil
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.float_util import FloatUtil
from cl.runtime.primitive.int_util import IntUtil
from cl.runtime.primitive.limits import check_int_32
from cl.runtime.primitive.limits import check_int_54
from cl.runtime.primitive.long_util import LongUtil
from cl.runtime.primitive.primitive_util import PrimitiveUtil
from cl.runtime.primitive.time_util import TimeUtil
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.primitive.uuid_util import UuidUtil
from cl.runtime.records.for_dataclasses.data import Data
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import TPrimitive
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.bool_format_enum import BoolFormatEnum
from cl.runtime.serializers.bytes_format_enum import BytesFormatEnum
from cl.runtime.serializers.date_format_enum import DateFormatEnum
from cl.runtime.serializers.datetime_format_enum import DatetimeFormatEnum
from cl.runtime.serializers.float_format_enum import FloatFormatEnum
from cl.runtime.serializers.int_format_enum import IntFormatEnum
from cl.runtime.serializers.long_format_enum import LongFormatEnum
from cl.runtime.serializers.none_format_enum import NoneFormatEnum
from cl.runtime.serializers.string_format_enum import StringFormatEnum
from cl.runtime.serializers.time_format_enum import TimeFormatEnum
from cl.runtime.serializers.timestamp_format_enum import TimestampFormatEnum
from cl.runtime.serializers.uuid_format_enum import UuidFormatEnum


@dataclass(slots=True, kw_only=True)
class PrimitiveSerializer(Data):
    """Helper class for serialization and deserialization of primitive types."""

    none_format: NoneFormatEnum = required()
    """Serialization format for None (pass through without conversion if not set)."""

    string_format: StringFormatEnum = required()
    """Serialization format for str (pass through without conversion if not set)."""

    float_format: FloatFormatEnum = required()
    """Serialization format for float (pass through without conversion if not set)."""

    bool_format: BoolFormatEnum = required()
    """Serialization format for bool (pass through without conversion if not set)."""

    int_format: IntFormatEnum = required()
    """Serialization format for int (pass through without conversion if not set)."""

    long_format: LongFormatEnum = required()
    """Serialization format for long (pass through without conversion if not set)."""

    date_format: DateFormatEnum = required()
    """Serialization format for dt.date (pass through without conversion if not set)."""

    datetime_format: DatetimeFormatEnum = required()
    """Serialization format for dt.datetime (pass through without conversion if not set)."""

    time_format: TimeFormatEnum = required()
    """Serialization format for dt.time (pass through without conversion if not set)."""

    uuid_format: UuidFormatEnum = required()
    """Serialization format for UUID other than UUIDv7 (pass through without conversion if not set)."""

    timestamp_format: TimestampFormatEnum = required()
    """Serialization format for UUIDv7 unique timestamp (pass through without conversion if not set)."""

    bytes_format: BytesFormatEnum = required()
    """Serialization format for bytes (pass through without conversion if not set)."""

    def serialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """
        Serialize a primitive type to a string or another primitive type.

        Returns:
            A string or another serialization output such as int or None

        Args:
            data: An instance of primitive class from PRIMITIVE_CLASS_NAMES
            type_hint: Optional type chain to use for validation and to identify a type that shares
                       the same class with another type (e.g. long and int types share the int class)
        """

        # Get the class of data
        data_class_name = TypeUtil.name(data)

        # Get parameters from the type chain, considering the possibility that it may be None
        schema_type_name = type_hint.schema_type_name if type_hint is not None else None
        is_optional = type_hint.optional if type_hint is not None else None

        # Validate that schema_type_name is compatible with value_class_name if specified
        # Because the value of None is passed through, value_class_name NoneType is compatible with any schema_type_name
        if schema_type_name is not None and data_class_name != "NoneType" and schema_type_name != data_class_name:
            if schema_type_name == "long":
                if data_class_name != "int":
                    raise RuntimeError(
                        f"Type {schema_type_name} can only be stored using int class, " f"not {data_class_name} class."
                    )
            elif schema_type_name == "timestamp":
                if data_class_name != "UUID":
                    raise RuntimeError(
                        f"Type {schema_type_name} can only be stored using UUID class, "
                        f"not {data_class_name} class."
                    )
            elif data is not None and data_class_name != schema_type_name:
                raise RuntimeError(f"Type {schema_type_name} cannot be stored as {data_class_name} class.")

        # Serialize based on value_class_name, using schema_type_name to distinguish between types that share the same class
        if data is None:
            if type_hint is None or type_hint.schema_type_name == "NoneType" or is_optional:
                return None
            else:
                raise RuntimeError(f"Field value is None but type hint {type_hint.to_str()} does not allow it.")
        elif data_class_name == "str":
            # Return None for an empty string
            return data if data else None
        elif data_class_name == "float":
            if (value_format := self.float_format) == FloatFormatEnum.PASSTHROUGH:
                return data
            elif value_format == FloatFormatEnum.DEFAULT:
                return FloatUtil.format(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, FloatFormatEnum)
        elif data_class_name == "bool":
            if (value_format := self.bool_format) == BoolFormatEnum.PASSTHROUGH:
                return data
            elif value_format == BoolFormatEnum.DEFAULT:
                return BoolUtil.to_str_or_none(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, BoolFormatEnum)
        elif data_class_name == "int":
            if schema_type_name is not None and schema_type_name == "int":
                # Use methods that check that the value is in 32-bit signed integer range
                # if schema_type_name is specified and is int rather than long
                if (value_format := self.int_format) == IntFormatEnum.PASSTHROUGH:
                    check_int_32(data)
                    return data
                elif value_format == IntFormatEnum.DEFAULT:
                    return IntUtil.to_str(data)
                else:
                    raise ErrorUtil.enum_value_error(value_format, IntFormatEnum)
            elif schema_type_name is not None and schema_type_name == "long":
                # Use methods that check that the value is in 32-bit signed integer range
                # if schema_type_name is specified and is int rather than long
                if (value_format := self.long_format) == LongFormatEnum.PASSTHROUGH:
                    check_int_54(data)
                    return data
                elif value_format == LongFormatEnum.DEFAULT:
                    return LongUtil.to_str(data)
                else:
                    raise ErrorUtil.enum_value_error(value_format, LongFormatEnum)
            else:
                # Otherwise do not perform range checks
                if (value_format := self.long_format) == LongFormatEnum.PASSTHROUGH:
                    return data
                elif value_format == LongFormatEnum.DEFAULT:
                    return LongUtil.to_str(data)
                elif value_format == LongFormatEnum.BSON_INT_64:
                    return Int64(data)
                else:
                    raise ErrorUtil.enum_value_error(value_format, LongFormatEnum)
        elif data_class_name == "date":
            if (value_format := self.date_format) == DateFormatEnum.PASSTHROUGH:
                return data
            elif value_format == DateFormatEnum.DEFAULT:
                return DateUtil.to_str(data)
            elif value_format == DateFormatEnum.ISO_INT:
                return DateUtil.to_iso_int(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, DateFormatEnum)
        elif data_class_name == "time":
            if (value_format := self.time_format) == TimeFormatEnum.PASSTHROUGH:
                return data
            elif value_format == TimeFormatEnum.DEFAULT:
                return TimeUtil.to_str(data)
            elif value_format == TimeFormatEnum.ISO_INT:
                return TimeUtil.to_iso_int(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, TimeFormatEnum)
        elif data_class_name == "datetime":
            if (value_format := self.datetime_format) == DatetimeFormatEnum.PASSTHROUGH:
                return data
            elif value_format == DatetimeFormatEnum.DEFAULT:
                return DatetimeUtil.to_str(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, DatetimeFormatEnum)
        elif data_class_name == "UUID":
            if data.version != 7 or (schema_type_name is not None and schema_type_name == "UUID"):
                if (value_format := self.uuid_format) == UuidFormatEnum.PASSTHROUGH:
                    return data
                elif value_format == UuidFormatEnum.DEFAULT:
                    # Use the standard delimited UUID format
                    return UuidUtil.to_str(data)
                else:
                    raise ErrorUtil.enum_value_error(value_format, UuidFormatEnum)
            else:
                # Under else, value.version == 7 and schema_type_name != "UUID"
                if schema_type_name is not None and schema_type_name != "timestamp":
                    raise RuntimeError("For UUID version 7, only UUID or timestamp types are valid.")

                if (value_format := self.timestamp_format) == TimestampFormatEnum.PASSTHROUGH:
                    return data
                elif value_format == TimestampFormatEnum.DEFAULT:
                    # Use timestamp-hex UUIDv7 format
                    return Timestamp.from_uuid7(data)
                elif value_format == TimestampFormatEnum.UUID:
                    # Use the standard delimited UUID format
                    return UuidUtil.to_str(data)
                else:
                    raise ErrorUtil.enum_value_error(value_format, TimestampFormatEnum)
        elif data_class_name == "bytes":
            if (value_format := self.bytes_format) == BytesFormatEnum.PASSTHROUGH:
                return data
            elif value_format == BytesFormatEnum.DEFAULT:
                # Base64 encoding for bytes on a single line
                return base64.b64encode(data).decode("utf-8")  # TODO: Create BytesUtil
            elif value_format == BytesFormatEnum.MIME:
                # Base64 encoding for bytes with MIME line wrap convention at 76 characters, remove trailing EOL
                return base64.encodebytes(data).decode("utf-8").rstrip("\n")  # TODO: Create BytesUtil
            else:
                raise ErrorUtil.enum_value_error(value_format, BytesFormatEnum)
        else:
            raise RuntimeError(f"Class {data_class_name} cannot be serialized using {type(self).__name__}.")

    def deserialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """
        Deserialize a string or another primitive value such as int or None to an instance of type_name.

        Returns:
            An instance of type_name, which must be one of PRIMITIVE_CLASS_NAMES, including None

        Args:
            data: A string or another serialization output such as int or None
            type_hint: Type chain of size one to use for validation and to identify a type that shares
                        the same class with another type (e.g. long and int types share the int class)
        """

        # Get parameters from the type chain, considering the possibility that it may be None
        schema_type_name = type_hint.schema_type_name if type_hint is not None else None
        is_optional = type_hint.optional if type_hint is not None else None  # TODO: Add a check for optional if value is not provided

        # Check if data is empty and validate is_optional flag
        is_data_empty = data in [None, "", "null"]
        if is_data_empty and not is_optional:
            raise RuntimeError("Serialized data is empty but marked as required.")

        if schema_type_name == "NoneType":  # TODO: Review the logic for None
            if is_data_empty:
                # Treat an empty string and "null" as None
                return None
            else:
                raise self._deserialization_error(data, schema_type_name, self.none_format)
        elif schema_type_name == "str":
            if is_data_empty:
                # Treat an empty string and "null" as None
                return None
            else:
                if isinstance(data, str):
                    # Pass through string
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, self.string_format)
        elif schema_type_name == "float":
            if (value_format := self.float_format) in [FloatFormatEnum.PASSTHROUGH, FloatFormatEnum.DEFAULT]:
                # Accept additional input types in addition to the one generated by the serializer
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, str):
                    # Deserialize from string
                    return float(data)  # TODO: !!! Use FloatUtil
                elif isinstance(data, float):
                    # Also accept float
                    return data
                elif isinstance(data, int):
                    # Also accept int
                    return float(data)
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, FloatFormatEnum)
        elif schema_type_name == "bool":
            if (value_format := self.bool_format) == BoolFormatEnum.PASSTHROUGH:
                if data is None or isinstance(data, bool):
                    # Pass through None and bool
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == BoolFormatEnum.DEFAULT:
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, str):
                    # Deserialize from string
                    return BoolUtil.from_str(data)
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, BoolFormatEnum)
        elif schema_type_name == "int":
            if (value_format := self.int_format) in [IntFormatEnum.PASSTHROUGH, IntFormatEnum.DEFAULT]:
                # Accept both passthrough and default formats
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, str):
                    # Checks that value is within 32-bit signed integer range
                    return IntUtil.from_str(data)
                elif isinstance(data, int):
                    # Passthrough int after checking that value is within 32-bit signed integer range
                    check_int_32(data)
                    return data
                elif isinstance(data, float):
                    # Checks that the value is round and is within 32-bit signed integer range
                    return IntUtil.from_float(data)
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, IntFormatEnum)
        elif schema_type_name == "long":
            if (value_format := self.long_format) in [LongFormatEnum.PASSTHROUGH, LongFormatEnum.DEFAULT]:
                # Accept both passthrough and default formats
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, str):
                    return LongUtil.from_str(data)
                elif isinstance(data, int):
                    # Passthrough int after checking that value is within 54-bit signed integer range
                    # that can be represented exactly by a float
                    check_int_54(data)
                    return data
                elif isinstance(data, float):
                    # Checks that the value is round and is within 54-bit signed integer range
                    # that can be represented exactly by a float
                    return LongUtil.from_float(data)
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == LongFormatEnum.BSON_INT_64:
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, Int64):
                    return int(data)
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, LongFormatEnum)
        elif schema_type_name == "date":
            if (value_format := self.date_format) in [DateFormatEnum.PASSTHROUGH, DateFormatEnum.DEFAULT]:
                # Accept both passthrough and default formats
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, str):
                    # Date as string in ISO-8601 string format ("yyyy-mm-dd")
                    return DateUtil.from_str(data)
                elif isinstance(data, dt.date):
                    # Pass through dt.date
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == DateFormatEnum.ISO_INT:
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, str):
                    # Date as string in ISO int format without separators ("yyyymmdd")
                    return DateUtil.from_iso_int(int(data))
                elif isinstance(data, int):
                    # Date as int in ISO int format without separators (yyyymmdd)
                    return DateUtil.from_iso_int(data)
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, DateFormatEnum)
        elif schema_type_name == "time":
            if (value_format := self.time_format) in [TimeFormatEnum.PASSTHROUGH, TimeFormatEnum.DEFAULT]:
                # Accept both passthrough and default formats
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, str):
                    # Convert from string in ISO-8601 format with milliseconds ("hh:mm:ss.fff")
                    return TimeUtil.from_str(data)
                elif isinstance(data, dt.time):
                    # Pass through dt.time
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == TimeFormatEnum.ISO_INT:
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, str):
                    # Time as string in ISO int format without separators with milliseconds ("hhmmssfff")
                    return TimeUtil.from_iso_int(int(data))
                elif isinstance(data, int):
                    # Time as int in ISO int format without separators with milliseconds (hhmmssfff)
                    return TimeUtil.from_iso_int(data)
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, TimeFormatEnum)
        elif schema_type_name == "datetime":
            if (value_format := self.datetime_format) in [DatetimeFormatEnum.PASSTHROUGH, DatetimeFormatEnum.DEFAULT]:
                # Accept both passthrough and default formats
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, str):
                    # Convert from string in ISO-8601 format with milliseconds in UTC ("yyyy-mm-ddThh:mm:ss.fffZ")
                    return DatetimeUtil.from_str(data)
                elif isinstance(data, dt.datetime):
                    # Pass through dt.datetime
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, DatetimeFormatEnum)
        elif schema_type_name == "UUID":
            if (value_format := self.uuid_format) == UuidFormatEnum.PASSTHROUGH:
                if data is None or isinstance(data, UUID):
                    # Pass through None and UUID
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == UuidFormatEnum.DEFAULT:
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, str):
                    # Accepts both standard format for any UUID version and timestamp-hex format for version 7
                    return UuidUtil.from_str(data)
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, UuidFormatEnum)
        elif schema_type_name == "timestamp":
            if (value_format := self.timestamp_format) == TimestampFormatEnum.PASSTHROUGH:
                if data is None:
                    # Pass through None
                    return data
                elif isinstance(data, UUID):
                    # Pass through UUID after checking version
                    if data.version != 7:
                        raise RuntimeError("For timestamp type, only version 7 of UUID is valid.")
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == TimestampFormatEnum.DEFAULT:
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, str):
                    result = UuidUtil.from_str(data)
                    # Accepts both standard format for any UUID version and timestamp-hex format for version 7,
                    # perform an explicit check to ensure UUID version matches the subtype
                    if result.version != 7:
                        raise RuntimeError("For timestamp type, only version 7 of UUID is valid.")
                    return result
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == TimestampFormatEnum.UUID:
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, str):
                    if is_data_empty:
                        # Treat an empty string and "null" as None
                        return None
                    elif isinstance(data, str):
                        result = UuidUtil.from_str(data)
                        # Accepts both standard format for any UUID version and timestamp-hex format for version 7,
                        # perform an explicit check to ensure UUID version matches the subtype
                        if result.version != 7:
                            raise RuntimeError("For timestamp type, only version 7 of UUID is valid.")
                        return result
                    else:
                        raise self._deserialization_error(data, schema_type_name, value_format)
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, TimestampFormatEnum)
        elif schema_type_name == "bytes":
            if (value_format := self.bytes_format) == BytesFormatEnum.PASSTHROUGH:
                if data is None or isinstance(data, bytes):
                    # Pass through None and bytes
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == BytesFormatEnum.DEFAULT:
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, str):
                    # Base64 encoding for bytes, the decoder accepts any line wrap convention
                    return base64.b64decode(data)  # TODO: Create BytesUtil
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == BytesFormatEnum.MIME:
                if is_data_empty:
                    # Treat an empty string and "null" as None
                    return None
                elif isinstance(data, str):
                    # Base64 encoding for bytes, the decoder accepts any line wrap convention
                    return base64.b64decode(data)  # TODO: Create BytesUtil
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, BytesFormatEnum)
        else:
            value_class_name = TypeUtil.name(data)
            serializer_type_name = TypeUtil.name(self)
            raise RuntimeError(f"Class {value_class_name} cannot be serialized using {serializer_type_name}.")

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
