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

import pytest
import datetime as dt
from uuid import UUID
from bson import Int64
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.time_util import TimeUtil
from cl.runtime.serializers.primitive_serializers import PrimitiveSerializers


def test_roundtrip():
    """Test roundtrip serialization and deserialization of primitive types."""

    test_cases = [
        # NoneType
        ("NoneType", None, None, "", "null"),
        # String
        ("str", None, None),
        ("str", "abc", "abc"),
        # Float
        ("float", None, None),
        ("float", 1.0, "1."),
        ("float", -1.23, "-1.23"),
        # Bool
        ("bool", None, None),
        ("bool", True, "true"),
        ("bool", False, "false"),
        # Int
        ("int", None, None),
        ("int", 123, "123"),
        ("int", -123, "-123"),
        # Date
        ("date", None, None),
        ("date", dt.date(2023, 4, 21), "2023-04-21"),
        # Time
        ("time", None, None),
        ("time", TimeUtil.from_fields(11, 10, 0), "11:10:00.000"),
        ("time", TimeUtil.from_fields(11, 10, 0, millisecond=123), "11:10:00.123"),
        # Datetime
        ("datetime", None, None),
        (
            "datetime",
            DatetimeUtil.from_fields(2023, 4, 21, 11, 10, 0),
            "2023-04-21T11:10:00.000Z",
        ),
        (
            "datetime",
            DatetimeUtil.from_fields(2023, 4, 21, 11, 10, 0, millisecond=123),
            "2023-04-21T11:10:00.123Z",
        ),
        # UUID
        ("UUID", None, None),
        ("UUID", UUID("1A" * 16), "1a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a"),
        # Timestamp
        ("timestamp", None, None),
        # ("timestamp", UUID("1A" * 16), "1a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a"),
        # TODO: Add datetime-hex format for timestamp
        # Bytes
        ("bytes", bytes([100, 110, 120]), "ZG54"),
        (
            "bytes",
            bytes(40 * [100, 110, 120]),
            "ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54\n"
            "ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54\n"
            "ZG54ZG54",
        ),
    ]

    for test_case in test_cases:

        # Get type_name, value, expected serialized value, and an optional list of alternative serialized values
        type_name, value, serialized, *alternative_serialized_list = test_case

        # Test passthrough with and without type_name
        assert PrimitiveSerializers.PASSTHROUGH.serialize(value) == value
        assert PrimitiveSerializers.PASSTHROUGH.serialize(value, [type_name]) == value

        # Serialize without type_name, deserialization always requires type_name
        assert PrimitiveSerializers.DEFAULT.serialize(value) == serialized
        assert PrimitiveSerializers.DEFAULT.deserialize(serialized, [type_name]) == value

        # Serialize and deserialize with type_name
        assert PrimitiveSerializers.DEFAULT.serialize(value, [type_name]) == serialized
        assert PrimitiveSerializers.DEFAULT.deserialize(serialized, [type_name]) == value

        # Test alternative serialized forms
        if alternative_serialized_list:
            for alternative_serialized in alternative_serialized_list:
                assert PrimitiveSerializers.DEFAULT.deserialize(alternative_serialized, [type_name]) == value


def test_mongo():
    """Test roundtrip serialization and deserialization using MongoDB settings."""

    test_cases = [
        # long
        ("long", None, None),
        ("long", 12345, Int64(12345)),
        ("long", 9007199254740991, Int64(9007199254740991)),  # Max int54
        # Date
        ("date", None, None),
        ("date", dt.date(2023, 4, 21), 20230421, "20230421"),
        # Time
        ("time", None, None),
        ("time", TimeUtil.from_fields(11, 10, 0), 111000000, "111000000"),
        ("time", TimeUtil.from_fields(11, 10, 0, millisecond=123), 111000123, "111000123"),
    ]

    for test_case in test_cases:

        # Get type_name, value, expected serialized value, and an optional list of alternative serialized values
        type_name, value, serialized, *alternative_serialized_list = test_case

        # Serialize without type_name, deserialization always requires type_name
        assert PrimitiveSerializers.FOR_MONGO.serialize(value) == serialized
        assert PrimitiveSerializers.FOR_MONGO.deserialize(serialized, [type_name]) == value

        # Serialize and deserialize with type_name
        assert PrimitiveSerializers.FOR_MONGO.serialize(value, [type_name]) == serialized
        assert PrimitiveSerializers.FOR_MONGO.deserialize(serialized, [type_name]) == value

        # Test alternative serialized forms
        if alternative_serialized_list:
            for alternative_serialized in alternative_serialized_list:
                assert PrimitiveSerializers.FOR_MONGO.deserialize(alternative_serialized, [type_name]) == value


def test_serialization_exceptions():
    """Test roundtrip serialization and deserialization."""

    test_cases = [
        # NoneType
        ("NoneType", ""),
        ("NoneType", "null"),
        # Bool
        ("bool", 0),
        ("bool", "None"),
        ("bool", "Null"),
        ("int", 2147483648),  # Out of range for int32
        ("long", 9007199254740992),  # Out of range for int54
    ]

    # Check exception cases with type name (without type name, the call will succeed for most values)
    for test_case in test_cases:
        type_name, value = test_case

        # Test passthrough with type_name
        with pytest.raises(Exception):
            print(value)
            PrimitiveSerializers.PASSTHROUGH.serialize(value, [type_name])

        # Test default settings with type_name
        with pytest.raises(Exception):
            PrimitiveSerializers.DEFAULT.serialize(value, [type_name])


def test_deserialization_exceptions():
    """Test roundtrip serialization and deserialization."""

    test_cases = [
        # NoneType
        ("NoneType", "None"),
        # Bool
        ("bool", 0),
        ("bool", "None"),
        ("bool", "Null"),
        ("bool", "True"),
        ("bool", "False"),
        ("bool", "Y"),
        ("bool", "N"),
        ("bool", "YES"),
        ("bool", "NO"),  # Norway problem
        ("int", "2147483648"),  # Out of range for int32
        ("long", "9007199254740992"),  # Out of range for int54
    ]

    # Check exception cases
    for test_case in test_cases:
        type_name, serialized = test_case
        with pytest.raises(Exception):
            PrimitiveSerializers.PASSTHROUGH.deserialize(serialized, [type_name])
        with pytest.raises(Exception):
            PrimitiveSerializers.DEFAULT.deserialize(serialized, [type_name])


if __name__ == "__main__":
    pytest.main([__file__])
