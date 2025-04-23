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
from cl.runtime.serializers.bootstrap_serializer import BootstrapSerializer
from cl.runtime.serializers.bytes_format import BytesFormat
from cl.runtime.serializers.date_format import DateFormat
from cl.runtime.serializers.datetime_format import DatetimeFormat
from cl.runtime.serializers.enum_format import EnumFormat
from cl.runtime.serializers.float_format import FloatFormat
from cl.runtime.serializers.int_format import IntFormat
from cl.runtime.serializers.json_encoders import JsonEncoders
from cl.runtime.serializers.long_format import LongFormat
from cl.runtime.serializers.none_format import NoneFormat
from cl.runtime.serializers.string_format import StringFormat
from cl.runtime.serializers.time_format import TimeFormat
from cl.runtime.serializers.timestamp_format import TimestampFormat
from cl.runtime.serializers.uuid_format import UuidFormat
from cl.runtime.serializers.yaml_encoders import YamlEncoders


class BootstrapSerializers:
    """Serialization without including or relying on type information, deserialization is not possible."""

    YAML = BootstrapSerializer(
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
        enum_format=EnumFormat.DEFAULT,
        encoder=YamlEncoders.DEFAULT,
    ).build()
    """Default settings with YAML output."""

    JSON = BootstrapSerializer(
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
        enum_format=EnumFormat.DEFAULT,
        encoder=JsonEncoders.DEFAULT,
    ).build()
    """Default settings with JSON output."""

    FOR_UI = BootstrapSerializer(
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
        bytes_format=BytesFormat.DEFAULT,
        enum_format=EnumFormat.DEFAULT,
        pascalize_keys=True,
    ).build()
    """Default bidirectional data serializer settings for UI."""
