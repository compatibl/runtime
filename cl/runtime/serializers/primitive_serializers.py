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

from cl.runtime.serializers.bool_format import BoolFormat
from cl.runtime.serializers.bytes_format import BytesFormat
from cl.runtime.serializers.date_format import DateFormat
from cl.runtime.serializers.datetime_format import DatetimeFormat
from cl.runtime.serializers.float_format import FloatFormat
from cl.runtime.serializers.int_format import IntFormat
from cl.runtime.serializers.long_format import LongFormat
from cl.runtime.serializers.none_format import NoneFormat
from cl.runtime.serializers.primitive_serializer import PrimitiveSerializer
from cl.runtime.serializers.string_format import StringFormat
from cl.runtime.serializers.time_format import TimeFormat
from cl.runtime.serializers.timestamp_format import TimestampFormat
from cl.runtime.serializers.type_format import TypeFormat
from cl.runtime.serializers.uuid_format import UuidFormat


class PrimitiveSerializers:
    """Standard combinations of primitive formats."""

    PASSTHROUGH = PrimitiveSerializer(
        none_format=NoneFormat.PASSTHROUGH,
        string_format=StringFormat.PASSTHROUGH,
        float_format=FloatFormat.PASSTHROUGH,
        bool_format=BoolFormat.PASSTHROUGH,
        int_format=IntFormat.PASSTHROUGH,
        long_format=LongFormat.PASSTHROUGH,
        date_format=DateFormat.PASSTHROUGH,
        time_format=TimeFormat.PASSTHROUGH,
        datetime_format=DatetimeFormat.PASSTHROUGH,
        uuid_format=UuidFormat.PASSTHROUGH,
        timestamp_format=TimestampFormat.PASSTHROUGH,
        bytes_format=BytesFormat.PASSTHROUGH,
        type_format=TypeFormat.PASSTHROUGH,
    ).build()
    """Do not perform any conversion but validate against type information if provided."""

    DEFAULT = PrimitiveSerializer(
        none_format=NoneFormat.PASSTHROUGH,
        string_format=StringFormat.PASSTHROUGH,
        float_format=FloatFormat.DEFAULT,
        bool_format=BoolFormat.DEFAULT,
        int_format=IntFormat.DEFAULT,
        long_format=LongFormat.DEFAULT,
        date_format=DateFormat.DEFAULT,
        time_format=TimeFormat.DEFAULT,
        datetime_format=DatetimeFormat.DEFAULT,
        uuid_format=UuidFormat.DEFAULT,
        timestamp_format=TimestampFormat.DEFAULT,
        bytes_format=BytesFormat.MIME,
        type_format=TypeFormat.DEFAULT,
    ).build()
    """Pass through None and string, serialize all other primitive types to string using default format."""

    FOR_JSON = PrimitiveSerializer(
        none_format=NoneFormat.PASSTHROUGH,
        string_format=StringFormat.PASSTHROUGH,
        float_format=FloatFormat.PASSTHROUGH,
        bool_format=BoolFormat.PASSTHROUGH,
        int_format=IntFormat.PASSTHROUGH,
        long_format=LongFormat.PASSTHROUGH,
        date_format=DateFormat.DEFAULT,
        time_format=TimeFormat.DEFAULT,
        datetime_format=DatetimeFormat.DEFAULT,
        uuid_format=UuidFormat.DEFAULT,
        timestamp_format=TimestampFormat.DEFAULT,
        bytes_format=BytesFormat.COMPACT,
        type_format=TypeFormat.DEFAULT,
    ).build()
    """Default primitive serializer settings for JSON."""

    FOR_UI = PrimitiveSerializer(
        none_format=NoneFormat.PASSTHROUGH,
        string_format=StringFormat.PASSTHROUGH,
        float_format=FloatFormat.PASSTHROUGH,
        bool_format=BoolFormat.PASSTHROUGH,
        int_format=IntFormat.DEFAULT,  # TODO: Review, should be passthrough
        long_format=LongFormat.DEFAULT,  # TODO: Review, should be passthrough
        date_format=DateFormat.DEFAULT,
        time_format=TimeFormat.DEFAULT,
        datetime_format=DatetimeFormat.DEFAULT,
        uuid_format=UuidFormat.DEFAULT,
        timestamp_format=TimestampFormat.UUID,  # TODO: Review, should accept DEFAULT
        bytes_format=BytesFormat.COMPACT,
        type_format=TypeFormat.DEFAULT,
    ).build()
    """Default primitive serializer settings for UI."""

    FOR_CSV = PrimitiveSerializer(
        none_format=NoneFormat.PASSTHROUGH,
        string_format=StringFormat.PASSTHROUGH,
        float_format=FloatFormat.PASSTHROUGH,
        bool_format=BoolFormat.DEFAULT,  # TODO: Review, should be passthrough
        int_format=IntFormat.PASSTHROUGH,
        long_format=LongFormat.PASSTHROUGH,
        date_format=DateFormat.DEFAULT,
        time_format=TimeFormat.DEFAULT,
        datetime_format=DatetimeFormat.DEFAULT,  # TODO: Support float for Excel?
        uuid_format=UuidFormat.DEFAULT,
        timestamp_format=TimestampFormat.UUID,  # TODO: Review, should accept DEFAULT
        bytes_format=BytesFormat.COMPACT,
        type_format=TypeFormat.DEFAULT,
    ).build()
    """Default primitive serializer settings for CSV."""

    FOR_SQLITE = PrimitiveSerializer(
        none_format=NoneFormat.PASSTHROUGH,
        string_format=StringFormat.PASSTHROUGH,
        float_format=FloatFormat.PASSTHROUGH,
        bool_format=BoolFormat.DEFAULT,  # TODO: Review, should be passthrough
        int_format=IntFormat.PASSTHROUGH,
        long_format=LongFormat.PASSTHROUGH,
        date_format=DateFormat.DEFAULT,
        time_format=TimeFormat.DEFAULT,
        datetime_format=DatetimeFormat.DEFAULT,
        uuid_format=UuidFormat.DEFAULT,
        timestamp_format=TimestampFormat.UUID,  # TODO: Review, should accept DEFAULT
        bytes_format=BytesFormat.COMPACT,
        type_format=TypeFormat.DEFAULT,
    ).build()
    """Default primitive serializer settings for SQLite."""

    FOR_MONGO = PrimitiveSerializer(
        none_format=NoneFormat.PASSTHROUGH,
        string_format=StringFormat.PASSTHROUGH,
        float_format=FloatFormat.PASSTHROUGH,
        bool_format=BoolFormat.PASSTHROUGH,
        int_format=IntFormat.PASSTHROUGH,
        long_format=LongFormat.BSON_INT_64,  # Uses NumberLong format in MongoDB
        date_format=DateFormat.ISO_INT,  # Uses readable int format in MongoDB
        time_format=TimeFormat.ISO_INT,  # Uses readable int format in MongoDB
        datetime_format=DatetimeFormat.PASSTHROUGH,
        uuid_format=UuidFormat.PASSTHROUGH,
        timestamp_format=TimestampFormat.PASSTHROUGH,
        bytes_format=BytesFormat.PASSTHROUGH,
        type_format=TypeFormat.DEFAULT,
    ).build()
    """
    Default primitive serializer settings for MongoDB.
    - Pass through None, str, float, bool, int, datetime, uuid, timestamp, bytes
    - Serialize long to np.int64
    - Serialize date and time to readable ISO int format
    - Serialize all other primitive type to string using default format
    """
