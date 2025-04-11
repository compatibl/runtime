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
from types import NoneType
from uuid import UUID
from bson import Int64
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.time_util import TimeUtil
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.primitive_serializers import PrimitiveSerializers


def test_roundtrip():
    """Test roundtrip serialization and deserialization of primitive types."""

    test_cases = [
        # NoneType
        (NoneType, "NoneType", None, None, "", "null"),
        # String
        (str, "str", None, None),
        (str, "str", "abc", "abc"),
        # Float
        (float, "float", None, None),
        (float, "float", 1.0, "1."),
        (float, "float", -1.23, "-1.23"),
        # Bool
        (bool, "bool", None, None),
        (bool, "bool", True, "true"),
        (bool, "bool", False, "false"),
        # Int
        (int, "int", None, None),
        (int, "int", 123, "123"),
        (int, "int", -123, "-123"),
        # Date
        (dt.date, "date", None, None),
        (dt.date, "date", dt.date(2023, 4, 21), "2023-04-21"),
        # Time
        (dt.time, "time", None, None),
        (dt.time, "time", TimeUtil.from_fields(11, 10, 0), "11:10:00.000"),
        (dt.time, "time", TimeUtil.from_fields(11, 10, 0, millisecond=123), "11:10:00.123"),
        # Datetime
        (dt.datetime, "datetime", None, None),
        (
            dt.datetime,
            "datetime",
            DatetimeUtil.from_fields(2023, 4, 21, 11, 10, 0),
            "2023-04-21T11:10:00.000Z",
        ),
        (
            dt.datetime,
            "datetime",
            DatetimeUtil.from_fields(2023, 4, 21, 11, 10, 0, millisecond=123),
            "2023-04-21T11:10:00.123Z",
        ),
        # UUID
        (UUID, "UUID", None, None),
        (UUID, "UUID", UUID("1A" * 16), "1a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a"),
        # Timestamp
        (UUID, "timestamp", None, None),
        # ("timestamp", UUID("1A" * 16), "1a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a"),
        # TODO: Add datetime-hex format for timestamp
        # Bytes
        (bytes, "bytes", bytes([100, 110, 120]), "ZG54"),
        (
            bytes,
            "bytes",
            bytes(40 * [100, 110, 120]),
            "ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54\n"
            "ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54\n"
            "ZG54ZG54",
        ),
    ]

    for test_case in test_cases:

        # Get type_name, value, expected serialized value, and an optional list of alternative serialized values
        class_, type_name, value, serialized, *alternative_serialized_list = test_case
        type_hint = TypeHint(schema_type_name=type_name, _schema_class=class_, optional=(value is None))

        # Test passthrough with and without type_name
        assert PrimitiveSerializers.PASSTHROUGH.serialize(value) == value
        assert PrimitiveSerializers.PASSTHROUGH.serialize(value, type_hint) == value

        # Serialize without type_name, deserialization always requires type_name
        assert PrimitiveSerializers.DEFAULT.serialize(value) == serialized
        assert PrimitiveSerializers.DEFAULT.deserialize(serialized, type_hint) == value

        # Serialize and deserialize with type_name
        assert PrimitiveSerializers.DEFAULT.serialize(value, type_hint) == serialized
        assert PrimitiveSerializers.DEFAULT.deserialize(serialized, type_hint) == value

        # Test alternative serialized forms
        if alternative_serialized_list:
            for alternative_serialized in alternative_serialized_list:
                assert PrimitiveSerializers.DEFAULT.deserialize(alternative_serialized, type_hint) == value


def test_mongo():
    """Test roundtrip serialization and deserialization using MongoDB settings."""

    test_cases = [
        # long
        (int, "long", None, None),
        (int, "long", 12345, Int64(12345)),
        (int, "long", 9007199254740991, Int64(9007199254740991)),  # Max int54
        # Date
        (dt.date, "date", None, None),
        (dt.date, "date", dt.date(2023, 4, 21), 20230421, "20230421"),
        # Time
        (dt.time, "time", None, None),
        (dt.time, "time", TimeUtil.from_fields(11, 10, 0), 111000000, "111000000"),
        (dt.time, "time", TimeUtil.from_fields(11, 10, 0, millisecond=123), 111000123, "111000123"),
    ]

    for test_case in test_cases:

        # Get type_name, value, expected serialized value, and an optional list of alternative serialized values
        class_, type_name, value, serialized, *alternative_serialized_list = test_case
        type_hint = TypeHint(schema_type_name=type_name, _schema_class=class_, optional=(value is None))

        # Serialize without type_name, deserialization always requires type_name
        assert PrimitiveSerializers.FOR_MONGO.serialize(value) == serialized
        assert PrimitiveSerializers.FOR_MONGO.deserialize(serialized, type_hint) == value

        # Serialize and deserialize with type_name
        assert PrimitiveSerializers.FOR_MONGO.serialize(value, type_hint) == serialized
        assert PrimitiveSerializers.FOR_MONGO.deserialize(serialized, type_hint) == value

        # Test alternative serialized forms
        if alternative_serialized_list:
            for alternative_serialized in alternative_serialized_list:
                assert PrimitiveSerializers.FOR_MONGO.deserialize(alternative_serialized, type_hint) == value


def test_serialization_exceptions():
    """Test roundtrip serialization and deserialization."""

    test_cases = [
        # NoneType
        (NoneType, "NoneType", ""),
        (NoneType, "NoneType", "null"),
        # Bool
        (bool, "bool", 0),
        (bool, "bool", "None"),
        (bool, "bool", "Null"),
        (int, "int", 2147483648),  # Out of range for int32
        (int, "long", 9007199254740992),  # Out of range for int54
    ]

    # Check exception cases with type name (without type name, the call will succeed for most values)
    for test_case in test_cases:
        class_, type_name, value = test_case
        type_hint = TypeHint(schema_type_name=type_name, _schema_class=class_, optional=(value is None))

        # Test passthrough with type_name
        with pytest.raises(Exception):
            print(value)
            PrimitiveSerializers.PASSTHROUGH.serialize(value, type_hint)

        # Test default settings with type_name
        with pytest.raises(Exception):
            PrimitiveSerializers.DEFAULT.serialize(value, type_hint)


def test_deserialization_exceptions():
    """Test roundtrip serialization and deserialization."""

    test_cases = [
        # NoneType
        (NoneType, "NoneType", "None"),
        # Bool
        (bool, "bool", 0),
        (bool, "bool", "None"),
        (bool, "bool", "Null"),
        (bool, "bool", "True"),
        (bool, "bool", "False"),
        (bool, "bool", "Y"),
        (bool, "bool", "N"),
        (bool, "bool", "YES"),
        (bool, "bool", "NO"),  # Norway problem
        (int, "int", "2147483648"),  # Out of range for int32
        (int, "long", "9007199254740992"),  # Out of range for int54
    ]

    # Check exception cases
    for test_case in test_cases:
        class_, type_name, serialized = test_case
        type_hint = TypeHint(schema_type_name=type_name, _schema_class=class_, optional=(serialized is None))
        with pytest.raises(Exception):
            PrimitiveSerializers.PASSTHROUGH.deserialize(serialized, type_hint)
        with pytest.raises(Exception):
            PrimitiveSerializers.DEFAULT.deserialize(serialized, type_hint)


if __name__ == "__main__":
    pytest.main([__file__])
