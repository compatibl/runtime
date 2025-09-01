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
from typing import Any
from uuid import UUID
from bson import Int64
from cl.runtime.csv_util import CsvUtil
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.bool_util import BoolUtil
from cl.runtime.primitive.date_util import DateUtil
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.float_util import FloatUtil
from cl.runtime.primitive.int_util import IntUtil
from cl.runtime.primitive.limits import check_int_32
from cl.runtime.primitive.limits import check_int_54
from cl.runtime.primitive.long_util import LongUtil
from cl.runtime.primitive.time_util import TimeUtil
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.primitive.uuid_util import UuidUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.none_checks import NoneChecks
from cl.runtime.records.protocols import PrimitiveTypes, is_empty
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.bool_format import BoolFormat
from cl.runtime.serializers.bytes_format import BytesFormat
from cl.runtime.serializers.date_format import DateFormat
from cl.runtime.serializers.datetime_format import DatetimeFormat
from cl.runtime.serializers.float_format import FloatFormat
from cl.runtime.serializers.int_format import IntFormat
from cl.runtime.serializers.long_format import LongFormat
from cl.runtime.serializers.none_format import NoneFormat
from cl.runtime.serializers.serializer import Serializer
from cl.runtime.serializers.string_format import StringFormat
from cl.runtime.serializers.time_format import TimeFormat
from cl.runtime.serializers.timestamp_format import TimestampFormat
from cl.runtime.serializers.type_format import TypeFormat
from cl.runtime.serializers.uuid_format import UuidFormat


@dataclass(slots=True, kw_only=True)
class PrimitiveSerializer(Serializer):
    """Helper class for serialization and deserialization of primitive types."""

    none_format: NoneFormat = required()
    """Serialization format for None."""

    string_format: StringFormat = required()
    """Serialization format for str."""

    float_format: FloatFormat = required()
    """Serialization format for float."""

    bool_format: BoolFormat = required()
    """Serialization format for bool."""

    int_format: IntFormat = required()
    """Serialization format for int."""

    long_format: LongFormat = required()
    """Serialization format for long."""

    date_format: DateFormat = required()
    """Serialization format for dt.date."""

    datetime_format: DatetimeFormat = required()
    """Serialization format for dt.datetime."""

    time_format: TimeFormat = required()
    """Serialization format for dt.time."""

    uuid_format: UuidFormat = required()
    """Serialization format for UUID other than UUIDv7."""

    timestamp_format: TimestampFormat = required()
    """Serialization format for UUIDv7 unique timestamp."""

    bytes_format: BytesFormat = required()
    """Serialization format for bytes."""

    type_format: TypeFormat = required()
    """Format of the type information in serialized data."""

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

        # Handle None or empty data first
        if is_empty(data):
            # Set to True if type hint is not specified
            is_optional = type_hint.optional if type_hint is not None else True
            if (value_format := self.none_format) == NoneFormat.PASSTHROUGH:
                if is_optional:
                    return None
                else:
                    raise RuntimeError(f"Field value is None but type hint {type_hint.to_str()} does not allow it.")
            else:
                raise ErrorUtil.enum_value_error(value_format, NoneFormat)

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
            raise RuntimeError(
                f"Data type '{data_class_name}' cannot be stored in a field declared as '{schema_type_name}'."
            )

        # Validate that subtype is compatible with schema_type_name
        subtype = type_hint.subtype if type_hint is not None else None
        if (
            (schema_type_name == "int" and subtype not in (None, "long")) or
            (schema_type_name == "str" and subtype not in (None, "timestamp"))
        ):
            raise RuntimeError(f"Subtype '{subtype}' cannot be stored in class '{schema_type_name}'.")

        # Serialize based schema_type_name, taking into account subtype
        if schema_type_name == "str":
            if (value_format := self.string_format) == StringFormat.PASSTHROUGH:
                # Return None for an empty string
                return data if data else None
            else:
                raise ErrorUtil.enum_value_error(value_format, StringFormat)
        elif schema_type_name == "float":
            if (value_format := self.float_format) == FloatFormat.PASSTHROUGH:
                return data
            elif value_format == FloatFormat.DEFAULT:
                return FloatUtil.format(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, FloatFormat)
        elif schema_type_name == "bool":
            if (value_format := self.bool_format) == BoolFormat.PASSTHROUGH:
                return data
            elif value_format == BoolFormat.DEFAULT:
                return BoolUtil.to_str_or_none(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, BoolFormat)
        elif schema_type_name == "int":
            if subtype is None:
                # Use methods that check that the value is in 32-bit signed integer range if subtype is not specified
                # if schema_type_name is specified and is int rather than long
                if (value_format := self.int_format) == IntFormat.PASSTHROUGH:
                    check_int_32(data)
                    return data
                elif value_format == IntFormat.DEFAULT:
                    return IntUtil.to_str(data)
                else:
                    raise ErrorUtil.enum_value_error(value_format, IntFormat)
            elif subtype == "long":
                # Use methods that check that the value is in 54-bit signed integer range if subtype == "long"
                # if schema_type_name is specified and is long
                if (value_format := self.long_format) == LongFormat.PASSTHROUGH:
                    check_int_54(data)
                    return data
                elif value_format == LongFormat.DEFAULT:
                    return LongUtil.to_str(data)
                elif value_format == LongFormat.BSON_INT_64:
                    return Int64(data)
                else:
                    raise ErrorUtil.enum_value_error(value_format, LongFormat)
            else:
                raise RuntimeError(f"Subtype {subtype} is not valid for type '{schema_type_name}'.")
        elif schema_type_name == "date":
            if (value_format := self.date_format) == DateFormat.PASSTHROUGH:
                return data
            elif value_format == DateFormat.DEFAULT:
                return DateUtil.to_str(data)
            elif value_format == DateFormat.ISO_INT:
                return DateUtil.to_iso_int(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, DateFormat)
        elif schema_type_name == "time":
            if (value_format := self.time_format) == TimeFormat.PASSTHROUGH:
                return data
            elif value_format == TimeFormat.DEFAULT:
                return TimeUtil.to_str(data)
            elif value_format == TimeFormat.ISO_INT:
                return TimeUtil.to_iso_int(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, TimeFormat)
        elif schema_type_name == "datetime":
            if (value_format := self.datetime_format) == DatetimeFormat.PASSTHROUGH:
                return data
            elif value_format == DatetimeFormat.DEFAULT:
                return DatetimeUtil.to_str(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, DatetimeFormat)
        elif schema_type_name == "UUID":
            if (value_format := self.uuid_format) == UuidFormat.PASSTHROUGH:
                return data
            elif value_format == UuidFormat.DEFAULT:
                # Use the standard delimited UUID format
                return UuidUtil.to_str(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, UuidFormat)
        elif schema_type_name == "bytes":
            if (value_format := self.bytes_format) == BytesFormat.PASSTHROUGH:
                return data
            elif value_format == BytesFormat.DEFAULT:
                # Base64 encoding for bytes with MIME line wrap convention at 76 characters, remove trailing EOL
                return base64.encodebytes(data).decode("utf-8").rstrip("\n")  # TODO: Create BytesUtil
            elif value_format == BytesFormat.COMPACT:
                # Base64 encoding for bytes on a single line
                return base64.b64encode(data).decode("utf-8")  # TODO: Create BytesUtil
            else:
                raise ErrorUtil.enum_value_error(value_format, BytesFormat)
        elif schema_type_name == "type":
            # Check this is a known type
            TypeCache.guard_known_type(data)
            if (type_format := self.type_format) == TypeFormat.PASSTHROUGH:
                # Return type
                return data
            elif type_format == TypeFormat.DEFAULT:
                # Return type name
                return typename(data)
            else:
                raise ErrorUtil.enum_value_error(type_format, TypeFormat)
        else:
            raise RuntimeError(f"Class {schema_type_name} is not supported by {type(self).__name__}.")

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
        # Type hint is required for deserialization of primitive types
        NoneChecks.guard_not_none(type_hint)

        # Handle None and its supported serialized representations first
        if data in [None, "", "null"]:
            if (value_format := self.none_format) == NoneFormat.PASSTHROUGH:
                if type_hint.optional:
                    return None
                else:
                    type_hint_str = f" for type hint '{type_hint.to_str()}'." if type_hint else "."
                    raise RuntimeError(f"Serialized data is None or empty but marked as required{type_hint_str}")
            else:
                raise ErrorUtil.enum_value_error(value_format, NoneFormat)

        # Get schema type from the type hint
        schema_type_name = typename(type_hint.schema_type)

        # Ensure there is no remaining component (type hint is not a sequence or mapping)
        if type_hint.remaining:
            raise RuntimeError(
                f"Primitive type {schema_type_name} is incompatible with a composite type hint: {type_hint.to_str()}."
            )

        # Validate that subtype is compatible with schema_type_name
        subtype = type_hint.subtype
        if (
            (schema_type_name == "int" and subtype not in (None, "long")) or
            (schema_type_name == "str" and subtype not in (None, "timestamp"))
        ):
            raise RuntimeError(f"Subtype '{subtype}' cannot be stored in class '{schema_type_name}'.")

        # Deserialize based schema_type_name, taking into account subtype
        if schema_type_name == "str":
            if subtype is None:
                if (value_format := self.string_format) == StringFormat.PASSTHROUGH:
                    if isinstance(data, str):
                        # Deserialize from string, strip leading and trailing triple quotes if present
                        data = CsvUtil.strip_quotes(data)
                        return data
                    else:
                        raise self._deserialization_error(data, schema_type_name, self.string_format)
                else:
                    raise ErrorUtil.enum_value_error(value_format, StringFormat)
            elif subtype == "timestamp":
                if (value_format := self.string_format) == StringFormat.PASSTHROUGH:
                    if isinstance(data, str):
                        # Deserialize from string, strip leading and trailing triple quotes if present
                        data = CsvUtil.strip_quotes(data)
                        # Fast timestamp format validation without a full date validity check
                        Timestamp.guard_valid(data, fast=True)
                        return data
                    else:
                        raise self._deserialization_error(data, schema_type_name, self.string_format)
                else:
                    raise ErrorUtil.enum_value_error(value_format, StringFormat)
            else:
                raise RuntimeError(f"Subtype {subtype} is not valid for type '{schema_type_name}'.")
        elif schema_type_name == "float":
            if (value_format := self.float_format) in [FloatFormat.PASSTHROUGH, FloatFormat.DEFAULT]:
                # Accept additional input types in addition to the one generated by the serializer
                if isinstance(data, str):
                    # Deserialize from string, strip leading and trailing triple quotes if present
                    data = CsvUtil.strip_quotes(data)
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
                raise ErrorUtil.enum_value_error(value_format, FloatFormat)
        elif schema_type_name == "bool":
            if (value_format := self.bool_format) == BoolFormat.PASSTHROUGH:
                if data is None or isinstance(data, bool):
                    # Pass through None and bool
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == BoolFormat.DEFAULT:
                if isinstance(data, str):
                    # Deserialize from string
                    return BoolUtil.from_str(data)
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, BoolFormat)
        elif schema_type_name == "int":
            if subtype is None:
                if (value_format := self.int_format) in [IntFormat.PASSTHROUGH, IntFormat.DEFAULT]:
                    # Accept both passthrough and default formats
                    if isinstance(data, str):
                        # Deserialize from string, strip leading and trailing triple quotes if present
                        data = CsvUtil.strip_quotes(data)
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
                    raise ErrorUtil.enum_value_error(value_format, IntFormat)
            elif subtype == "long":
                if (value_format := self.long_format) in [LongFormat.PASSTHROUGH, LongFormat.DEFAULT]:
                    # Accept both passthrough and default formats
                    if isinstance(data, str):
                        # Deserialize from string, strip leading and trailing triple quotes if present
                        data = CsvUtil.strip_quotes(data)
                        # Checks that value is within 54-bit signed integer range
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
                elif value_format == LongFormat.BSON_INT_64:
                    if isinstance(data, Int64):
                        return int(data)
                    else:
                        raise self._deserialization_error(data, schema_type_name, value_format)
                else:
                    raise ErrorUtil.enum_value_error(value_format, LongFormat)
            else:
                raise RuntimeError(f"Subtype {subtype} is not valid for type '{schema_type_name}'.")
        elif schema_type_name == "date":
            if (value_format := self.date_format) in [DateFormat.PASSTHROUGH, DateFormat.DEFAULT]:
                # Accept both passthrough and default formats
                if isinstance(data, str):
                    # Deserialize from string, strip leading and trailing triple quotes if present
                    data = CsvUtil.strip_quotes(data)
                    # Date as string in ISO-8601 string format ("yyyy-mm-dd")
                    return DateUtil.from_str(data)
                elif isinstance(data, dt.date):
                    # Pass through dt.date
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == DateFormat.ISO_INT:
                if isinstance(data, str):
                    # Deserialize from string, strip leading and trailing triple quotes if present
                    data = CsvUtil.strip_quotes(data)
                    # Date as string in ISO int format without separators ("yyyymmdd")
                    return DateUtil.from_iso_int(int(data))
                elif isinstance(data, int):
                    # Date as int in ISO int format without separators (yyyymmdd)
                    return DateUtil.from_iso_int(data)
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, DateFormat)
        elif schema_type_name == "time":
            if (value_format := self.time_format) in [TimeFormat.PASSTHROUGH, TimeFormat.DEFAULT]:
                # Accept both passthrough and default formats
                if isinstance(data, str):
                    # Deserialize from string, strip leading and trailing triple quotes if present
                    data = CsvUtil.strip_quotes(data)
                    # Convert from string in ISO-8601 format with milliseconds ("hh:mm:ss.fff")
                    return TimeUtil.from_str(data)
                elif isinstance(data, dt.time):
                    # Pass through dt.time
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == TimeFormat.ISO_INT:
                if isinstance(data, str):
                    # Time as string in ISO int format without separators with milliseconds ("hhmmssfff")
                    return TimeUtil.from_iso_int(int(data))
                elif isinstance(data, int):
                    # Time as int in ISO int format without separators with milliseconds (hhmmssfff)
                    return TimeUtil.from_iso_int(data)
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, TimeFormat)
        elif schema_type_name == "datetime":
            if (value_format := self.datetime_format) in [DatetimeFormat.PASSTHROUGH, DatetimeFormat.DEFAULT]:
                # Accept both passthrough and default formats
                if isinstance(data, str):
                    # Deserialize from string, strip leading and trailing triple quotes if present
                    data = CsvUtil.strip_quotes(data)
                    # Convert from string in ISO-8601 format with milliseconds in UTC ("yyyy-mm-ddThh:mm:ss.fffZ")
                    return DatetimeUtil.from_str(data)
                elif isinstance(data, dt.datetime):
                    # Pass through dt.datetime
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, DatetimeFormat)
        elif schema_type_name == "UUID":
            if (value_format := self.uuid_format) == UuidFormat.PASSTHROUGH:
                if data is None or isinstance(data, UUID):
                    # Pass through None and UUID
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == UuidFormat.DEFAULT:
                if isinstance(data, str):
                    # Accepts both standard format for any UUID version and timestamp-hex format for version 7
                    return UuidUtil.from_str(data)
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, UuidFormat)
        elif schema_type_name == "bytes":
            if (value_format := self.bytes_format) == BytesFormat.PASSTHROUGH:
                if data is None or isinstance(data, bytes):
                    # Pass through None and bytes
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == BytesFormat.DEFAULT:
                if isinstance(data, str):
                    # Base64 encoding for bytes, the decoder accepts any line wrap convention
                    return base64.b64decode(data)  # TODO: Create BytesUtil
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == BytesFormat.COMPACT:
                if isinstance(data, str):
                    # Base64 encoding for bytes, the decoder accepts any line wrap convention
                    return base64.b64decode(data)  # TODO: Create BytesUtil
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, BytesFormat)
        elif schema_type_name == "type":
            if (value_format := self.type_format) == TypeFormat.PASSTHROUGH:
                if data is None:
                    # Pass through None
                    return None
                elif isinstance(data, type):
                    # Return data after checking it is a known type
                    assert TypeCache.guard_known_type(data)
                    return data
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            elif value_format == TypeFormat.DEFAULT:
                if isinstance(data, str):
                    # Get type from string typename, must be a known type
                    return TypeCache.from_type_name(data)
                else:
                    raise self._deserialization_error(data, schema_type_name, value_format)
            else:
                raise ErrorUtil.enum_value_error(value_format, TypeFormat)
        else:
            type_hint_str = f" in type hint '{type_hint.to_str()}' " if type_hint else " "
            raise RuntimeError(f"Type '{schema_type_name}'{type_hint_str}is not supported by {typename(type(self))}.")

    @classmethod
    def _deserialization_error(cls, value: PrimitiveTypes | None, type_name: str, type_format: IntEnum) -> Exception:
        """Error message on deserialization failure."""
        value_type_name = typename(type(value))
        value_format_str = f"{type_format.__class__} set to {type_format.name}"
        value_str = f"\n{value}\n" if isinstance(value, str) and "\n" in value else value
        return RuntimeError(
            f"{cls.__name__} cannot deserialize to type {type_name} with {value_format_str}.\n"
            f"Input value type: {value_type_name}\n"
            f"Input value: {value_str}"
        )
