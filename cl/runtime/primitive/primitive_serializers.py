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

from cl.runtime.primitive.bool_format_enum import BoolFormatEnum
from cl.runtime.primitive.bytes_format_enum import BytesFormatEnum
from cl.runtime.primitive.date_format_enum import DateFormatEnum
from cl.runtime.primitive.datetime_format_enum import DatetimeFormatEnum
from cl.runtime.primitive.float_format_enum import FloatFormatEnum
from cl.runtime.primitive.int_format_enum import IntFormatEnum
from cl.runtime.primitive.long_format_enum import LongFormatEnum
from cl.runtime.primitive.none_format_enum import NoneFormatEnum
from cl.runtime.primitive.string_format_enum import StringFormatEnum
from cl.runtime.primitive.time_format_enum import TimeFormatEnum
from cl.runtime.primitive.timestamp_format_enum import TimestampFormatEnum
from cl.runtime.primitive.uuid_format_enum import UuidFormatEnum
from cl.runtime.serializers.primitive_serializer import PrimitiveSerializer

cls = PrimitiveSerializer


class PrimitiveSerializers:
    """Standard combinations of primitive formats."""

    PASSTHROUGH: cls = cls(
        none_format=NoneFormatEnum.PASSTHROUGH,
        string_format=StringFormatEnum.PASSTHROUGH,
        float_format=FloatFormatEnum.PASSTHROUGH,
        bool_format=BoolFormatEnum.PASSTHROUGH,
        int_format=IntFormatEnum.PASSTHROUGH,
        long_format=LongFormatEnum.PASSTHROUGH,
        date_format=DateFormatEnum.PASSTHROUGH,
        datetime_format=DatetimeFormatEnum.PASSTHROUGH,
        time_format=TimeFormatEnum.PASSTHROUGH,
        uuid_format=UuidFormatEnum.PASSTHROUGH,
        timestamp_format=TimestampFormatEnum.PASSTHROUGH,
        bytes_format=BytesFormatEnum.PASSTHROUGH,
    ).build()
    """Pass through None and all primitive values without conversion."""

    DEFAULT: cls = cls(
        none_format=NoneFormatEnum.PASSTHROUGH,
        string_format=StringFormatEnum.PASSTHROUGH,
        float_format=FloatFormatEnum.DEFAULT,
        bool_format=BoolFormatEnum.DEFAULT,
        int_format=IntFormatEnum.DEFAULT,
        long_format=LongFormatEnum.DEFAULT,
        date_format=DateFormatEnum.DEFAULT,
        datetime_format=DatetimeFormatEnum.DEFAULT,
        time_format=TimeFormatEnum.DEFAULT,
        uuid_format=UuidFormatEnum.DEFAULT,
        timestamp_format=TimestampFormatEnum.DEFAULT,
        bytes_format=BytesFormatEnum.DEFAULT,
    ).build()
    """Pass through None and string, serialize all other primitive types to string using default format."""

    FOR_JSON: cls = cls(
        none_format=NoneFormatEnum.PASSTHROUGH,
        string_format=StringFormatEnum.PASSTHROUGH,
        float_format=FloatFormatEnum.PASSTHROUGH,
        bool_format=BoolFormatEnum.PASSTHROUGH,
        int_format=IntFormatEnum.PASSTHROUGH,
        long_format=LongFormatEnum.PASSTHROUGH,
        date_format=DateFormatEnum.PASSTHROUGH,
        datetime_format=DatetimeFormatEnum.PASSTHROUGH,
        time_format=TimeFormatEnum.PASSTHROUGH,
        uuid_format=UuidFormatEnum.PASSTHROUGH,
        timestamp_format=TimestampFormatEnum.PASSTHROUGH,
        bytes_format=BytesFormatEnum.PASSTHROUGH,
    ).build()
    """
    Default primitive serializer settings for JSON.
    """

    FOR_MONGO: cls = cls(
        none_format=NoneFormatEnum.PASSTHROUGH,
        string_format=StringFormatEnum.PASSTHROUGH,
        float_format=FloatFormatEnum.PASSTHROUGH,
        bool_format=BoolFormatEnum.PASSTHROUGH,
        int_format=IntFormatEnum.PASSTHROUGH,
        long_format=LongFormatEnum.PASSTHROUGH,
        date_format=DateFormatEnum.ISO_INT,
        datetime_format=DatetimeFormatEnum.PASSTHROUGH,
        time_format=TimeFormatEnum.ISO_INT,
        uuid_format=UuidFormatEnum.PASSTHROUGH,
        timestamp_format=TimestampFormatEnum.PASSTHROUGH,
        bytes_format=BytesFormatEnum.PASSTHROUGH,
    ).build()
    """
    Default primitive serializer settings for MongoDB.
    - Pass through None, str, float, bool, int, datetime, uuid, timestamp, bytes
    - Serialize long to np.int64
    - Serialize date and time to readable ISO int format
    - Serialize all other primitive type to string using default format
    """
