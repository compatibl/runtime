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

from cl.runtime.serializers.bool_format_enum import BoolFormatEnum
from cl.runtime.serializers.bytes_format_enum import BytesFormatEnum
from cl.runtime.serializers.date_format_enum import DateFormatEnum
from cl.runtime.serializers.datetime_format_enum import DatetimeFormatEnum
from cl.runtime.serializers.float_format_enum import FloatFormatEnum
from cl.runtime.serializers.int_format_enum import IntFormatEnum
from cl.runtime.serializers.long_format_enum import LongFormatEnum
from cl.runtime.serializers.none_format_enum import NoneFormatEnum
from cl.runtime.serializers.primitive_serializer import PrimitiveSerializer
from cl.runtime.serializers.string_format_enum import StringFormatEnum
from cl.runtime.serializers.time_format_enum import TimeFormatEnum
from cl.runtime.serializers.timestamp_format_enum import TimestampFormatEnum
from cl.runtime.serializers.uuid_format_enum import UuidFormatEnum

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
        time_format=TimeFormatEnum.PASSTHROUGH,
        datetime_format=DatetimeFormatEnum.PASSTHROUGH,
        uuid_format=UuidFormatEnum.PASSTHROUGH,
        timestamp_format=TimestampFormatEnum.PASSTHROUGH,
        bytes_format=BytesFormatEnum.PASSTHROUGH,
    ).build()
    """Do not perform any conversion but validate against type information if provided."""

    DEFAULT: cls = cls(
        none_format=NoneFormatEnum.PASSTHROUGH,
        string_format=StringFormatEnum.PASSTHROUGH,
        float_format=FloatFormatEnum.DEFAULT,
        bool_format=BoolFormatEnum.DEFAULT,
        int_format=IntFormatEnum.DEFAULT,
        long_format=LongFormatEnum.DEFAULT,
        date_format=DateFormatEnum.DEFAULT,
        time_format=TimeFormatEnum.DEFAULT,
        datetime_format=DatetimeFormatEnum.DEFAULT,
        uuid_format=UuidFormatEnum.DEFAULT,
        timestamp_format=TimestampFormatEnum.DEFAULT,
        bytes_format=BytesFormatEnum.MIME,
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
        time_format=TimeFormatEnum.PASSTHROUGH,
        datetime_format=DatetimeFormatEnum.PASSTHROUGH,
        uuid_format=UuidFormatEnum.PASSTHROUGH,
        timestamp_format=TimestampFormatEnum.PASSTHROUGH,
        bytes_format=BytesFormatEnum.PASSTHROUGH,
    ).build()
    """Default primitive serializer settings for JSON."""

    FOR_UI: cls = cls(
        none_format=NoneFormatEnum.PASSTHROUGH,
        string_format=StringFormatEnum.PASSTHROUGH,
        float_format=FloatFormatEnum.PASSTHROUGH,
        bool_format=BoolFormatEnum.PASSTHROUGH,
        int_format=IntFormatEnum.DEFAULT,  # TODO: Review, should be passthrough
        long_format=LongFormatEnum.DEFAULT,  # TODO: Review, should be passthrough
        date_format=DateFormatEnum.DEFAULT,
        time_format=TimeFormatEnum.DEFAULT,
        datetime_format=DatetimeFormatEnum.DEFAULT,
        uuid_format=UuidFormatEnum.DEFAULT,
        timestamp_format=TimestampFormatEnum.UUID,  # TODO: Review, should accept DEFAULT
        bytes_format=BytesFormatEnum.DEFAULT,
    ).build()
    """Default primitive serializer settings for UI."""

    FOR_CSV: cls = cls(
        none_format=NoneFormatEnum.PASSTHROUGH,
        string_format=StringFormatEnum.PASSTHROUGH,
        float_format=FloatFormatEnum.PASSTHROUGH,
        bool_format=BoolFormatEnum.DEFAULT,  # TODO: Review, should be passthrough
        int_format=IntFormatEnum.PASSTHROUGH,
        long_format=LongFormatEnum.PASSTHROUGH,
        date_format=DateFormatEnum.DEFAULT,
        time_format=TimeFormatEnum.DEFAULT,
        datetime_format=DatetimeFormatEnum.DEFAULT,  # TODO: Support float for Excel?
        uuid_format=UuidFormatEnum.DEFAULT,
        timestamp_format=TimestampFormatEnum.UUID,  # TODO: Review, should accept DEFAULT
        bytes_format=BytesFormatEnum.DEFAULT,
    ).build()
    """Default primitive serializer settings for UI."""

    FOR_SQLITE: cls = cls(
        none_format=NoneFormatEnum.PASSTHROUGH,
        string_format=StringFormatEnum.PASSTHROUGH,
        float_format=FloatFormatEnum.PASSTHROUGH,
        bool_format=BoolFormatEnum.DEFAULT,  # TODO: Review, should be passthrough
        int_format=IntFormatEnum.PASSTHROUGH,
        long_format=LongFormatEnum.PASSTHROUGH,
        date_format=DateFormatEnum.DEFAULT,
        time_format=TimeFormatEnum.PASSTHROUGH,
        datetime_format=DatetimeFormatEnum.DEFAULT,
        uuid_format=UuidFormatEnum.DEFAULT,
        timestamp_format=TimestampFormatEnum.UUID,  # TODO: Review, should accept DEFAULT
        bytes_format=BytesFormatEnum.DEFAULT,
    ).build()
    """Default primitive serializer settings for UI."""

    FOR_MONGO: cls = cls(
        none_format=NoneFormatEnum.PASSTHROUGH,
        string_format=StringFormatEnum.PASSTHROUGH,
        float_format=FloatFormatEnum.PASSTHROUGH,
        bool_format=BoolFormatEnum.PASSTHROUGH,
        int_format=IntFormatEnum.PASSTHROUGH,
        long_format=LongFormatEnum.PASSTHROUGH,
        date_format=DateFormatEnum.ISO_INT,
        time_format=TimeFormatEnum.ISO_INT,
        datetime_format=DatetimeFormatEnum.PASSTHROUGH,
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
