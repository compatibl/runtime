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
from dataclasses import dataclass
from cl.runtime.primitive.bool_format_enum import BoolFormatEnum
from cl.runtime.primitive.bool_util import BoolUtil
from cl.runtime.primitive.bytes_format_enum import BytesFormatEnum
from cl.runtime.primitive.date_format_enum import DateFormatEnum
from cl.runtime.primitive.date_util import DateUtil
from cl.runtime.primitive.datetime_format_enum import DatetimeFormatEnum
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.float_format_enum import FloatFormatEnum
from cl.runtime.primitive.float_util import FloatUtil
from cl.runtime.primitive.int_format_enum import IntFormatEnum
from cl.runtime.primitive.long_format_enum import LongFormatEnum
from cl.runtime.primitive.none_format_enum import NoneFormatEnum
from cl.runtime.primitive.string_format_enum import StringFormatEnum
from cl.runtime.primitive.time_format_enum import TimeFormatEnum
from cl.runtime.primitive.time_util import TimeUtil
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.primitive.timestamp_format_enum import TimestampFormatEnum
from cl.runtime.primitive.uuid_format_enum import UuidFormatEnum
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

    def serialize(self, value: TPrimitive | None) -> TPrimitive | None:
        """Serialize a primitive type to a string or another primitive type (return None if argument is None)."""
        # Use type name because different import libraries are possible for some of the primitive types such as UUID
        match type(value).__name__:
            case "NoneType":
                return None
            case "str":
                # Return None for an empty string
                return value if value else None
            case "float":
                match self.float_format:
                    case None:
                        return value
                    case FloatFormatEnum.DEFAULT:
                        return FloatUtil.format(value)
                    case _:
                        raise RuntimeError(f"No conversion is provided for {self.float_format}.")
            case "bool":
                match self.bool_format:
                    case None:
                        return value
                    case BoolFormatEnum.DEFAULT:
                        return BoolUtil.format(value)
                    case _:
                        raise RuntimeError(f"No conversion is provided for {self.bool_format}.")
            case "int":
                match self.int_format:
                    case None:
                        return value
                    case IntFormatEnum.DEFAULT:
                        return str(value)  # TODO: Use IntUtil
                    case _:
                        raise RuntimeError(f"No conversion is provided for {self.int_format}.")
            case "date":
                match self.date_format:
                    case None:
                        return value
                    case DateFormatEnum.DEFAULT:
                        return DateUtil.to_str(value)
                    case _:
                        raise RuntimeError(f"No conversion is provided for {self.date_format}.")
            case "time":
                match self.time_format:
                    case None:
                        return value
                    case TimeFormatEnum.DEFAULT:
                        return TimeUtil.to_str(value)
                    case _:
                        raise RuntimeError(f"No conversion is provided for {self.time_format}.")
            case "datetime":
                match self.datetime_format:
                    case None:
                        return value
                    case DatetimeFormatEnum.DEFAULT:
                        return DatetimeUtil.to_str(value)
                    case _:
                        raise RuntimeError(f"No conversion is provided for {self.datetime_format}.")
            case "UUID":
                if Timestamp.is_uuid7(value):
                    match self.timestamp_format:
                        case None:
                            return value
                        case TimestampFormatEnum.DEFAULT:
                            # Use timestamp format for UUIDv7
                            return Timestamp.from_uuid7(value)
                        case _:
                            raise RuntimeError(f"No conversion is provided for {self.timestamp_format}.")
                else:
                    match self.uuid_format:
                        case None:
                            return value
                        case UuidFormatEnum.DEFAULT:
                            # Use the standard format for other UUID types
                            return str(value)
                        case _:
                            raise RuntimeError(f"No conversion is provided for {self.uuid_format}.")
            case "bytes":
                match self.bytes_format:
                    case None:
                        return value
                    case BytesFormatEnum.DEFAULT:
                        # Base64 encoding for bytes with MIME line wrap convention at 76 characters, remove trailing EOL
                        return base64.encodebytes(value).decode("utf-8").rstrip("\n")
                    case _:
                        raise RuntimeError(f"No conversion is provided for {self.bytes_format}.")
            case _:
                raise RuntimeError(f"Type {TypeUtil.name(value)} cannot be serialized using PrimitiveSerializer.")

    def deserialize(self, value: TPrimitive | None) -> TPrimitive | None:
        """Deserialize a string or another primitive type to a primitive type (return None if argument is None)."""
        raise NotImplementedError()
