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
from dataclasses import dataclass
from types import NoneType
from typing import Any
from uuid import UUID
from bson import Int64
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.time_util import TimeUtil
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.primitive_serializers import PrimitiveSerializers
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass


@dataclass(slots=True, kw_only=True)
class _TestCase:
    """Represents a single test case for serialization and deserialization."""

    type_: type
    """Data type."""

    subtype: str | None = None
    """Data subtype if present, None otherwise."""

    value: Any
    """Value before serialization."""

    serialized: Any | None = None
    """Value after serialization (optional, do not specify for exception case testing)."""

    alternative_serialized: list[Any] | None = None
    """Alternative serialized values that are deserialized to the same value (optional)."""

    def get_type_hint(self) -> TypeHint:
        """Get type hint for the test."""
        return TypeHint(
            schema_type=self.type_, optional=(self.value is None), predicate=None, remaining=None, subtype=self.subtype
        )


def test_roundtrip():
    """Test roundtrip serialization and deserialization of primitive types."""

    test_cases = [
        # String
        _TestCase(type_=str, value=None, serialized=None, alternative_serialized=("", "null")),
        _TestCase(type_=str, value="abc", serialized="abc"),
        # Float
        _TestCase(type_=float, value=None, serialized=None, alternative_serialized=("", "null")),
        _TestCase(type_=float, value=1.0, serialized="1."),
        _TestCase(type_=float, value=-1.23, serialized="-1.23"),
        # Bool
        _TestCase(type_=bool, value=None, serialized=None, alternative_serialized=("", "null")),
        _TestCase(type_=bool, value=True, serialized="true"),
        _TestCase(type_=bool, value=False, serialized="false"),
        # Int
        _TestCase(type_=int, value=None, serialized=None, alternative_serialized=("", "null")),
        _TestCase(type_=int, value=123, serialized="123"),
        _TestCase(type_=int, value=-123, serialized="-123"),
        # Date
        _TestCase(type_=dt.date, value=None, serialized=None, alternative_serialized=("", "null")),
        _TestCase(type_=dt.date, value=dt.date(2023, 4, 21), serialized="2023-04-21"),
        # Time
        _TestCase(type_=dt.time, value=None, serialized=None, alternative_serialized=("", "null")),
        _TestCase(type_=dt.time, value=TimeUtil.from_fields(11, 10, 0), serialized="11:10:00.000"),
        _TestCase(type_=dt.time, value=TimeUtil.from_fields(11, 10, 0, millisecond=123), serialized="11:10:00.123"),
        # Datetime
        _TestCase(type_=dt.datetime, value=None, serialized=None, alternative_serialized=("", "null")),
        _TestCase(
            type_=dt.datetime,
            value=DatetimeUtil.from_fields(2023, 4, 21, 11, 10, 0),
            serialized="2023-04-21T11:10:00.000Z",
        ),
        _TestCase(
            type_=dt.datetime,
            value=DatetimeUtil.from_fields(2023, 4, 21, 11, 10, 0, millisecond=123),
            serialized="2023-04-21T11:10:00.123Z",
        ),
        # UUID
        _TestCase(type_=UUID, value=None, serialized=None, alternative_serialized=("", "null")),
        _TestCase(type_=UUID, value=UUID("1A" * 16), serialized="1a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a"),
        # Timestamp
        _TestCase(type_=str, subtype="timestamp", value=None, serialized=None, alternative_serialized=("", "null")),
        # TODO: Add datetime-hex sample for timestamp
        # TODO: ! Restore _TestCase(type_=str, subtype="timestamp", value=UUID("1A" * 16), serialized="1a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a",),
        # Bytes
        _TestCase(type_=bytes, value=bytes([100, 110, 120]), serialized="ZG54"),
        _TestCase(
            type_=bytes,
            value=bytes(40 * [100, 110, 120]),
            serialized="ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54\n"
            "ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54ZG54\n"
            "ZG54ZG54",
        ),
        _TestCase(type_=type, value=StubDataclass, serialized="StubDataclass"),
    ]

    for test_case in test_cases:

        # Get type hint from the test case
        type_hint = test_case.get_type_hint()

        # Test passthrough with and without type_name
        assert PrimitiveSerializers.PASSTHROUGH.serialize(test_case.value) == test_case.value
        assert PrimitiveSerializers.PASSTHROUGH.serialize(test_case.value, type_hint) == test_case.value

        # Serialize without type_name, deserialization always requires type_name
        assert PrimitiveSerializers.DEFAULT.serialize(test_case.value) == test_case.serialized
        assert PrimitiveSerializers.DEFAULT.deserialize(test_case.serialized, type_hint) == test_case.value

        # Serialize and deserialize with type_name
        assert PrimitiveSerializers.DEFAULT.serialize(test_case.value, type_hint) == test_case.serialized
        assert PrimitiveSerializers.DEFAULT.deserialize(test_case.serialized, type_hint) == test_case.value

        # Test alternative serialized forms
        if test_case.alternative_serialized:
            for alternative_serialized in test_case.alternative_serialized:
                assert PrimitiveSerializers.DEFAULT.deserialize(alternative_serialized, type_hint) == test_case.value


def test_mongo():
    """Test roundtrip serialization and deserialization using MongoDB settings."""

    test_cases = [
        # long
        _TestCase(type_=int, subtype="long", value=None, serialized=None),
        _TestCase(type_=int, subtype="long", value=12345, serialized=Int64(12345)),
        _TestCase(type_=int, subtype="long", value=9007199254740991, serialized=Int64(9007199254740991)),  # Max int54
        # Date,
        _TestCase(type_=dt.date, value=None, serialized=None),
        _TestCase(type_=dt.date, value=dt.date(2023, 4, 21), serialized=20230421, alternative_serialized=("20230421",)),
        # Time
        _TestCase(type_=dt.time, value=None, serialized=None),
        _TestCase(
            type_=dt.time,
            value=TimeUtil.from_fields(11, 10, 0, millisecond=123),
            serialized=111000123,
            alternative_serialized=("111000123",),
        ),
    ]

    for test_case in test_cases:

        # Get type hint from the test case
        type_hint = test_case.get_type_hint()

        # Serialize without type_name, deserialization always requires type_name
        if test_case.subtype is None:
            # Exclude cases with subtype from the test without type hint
            assert PrimitiveSerializers.FOR_MONGO.serialize(test_case.value) == test_case.serialized
        assert PrimitiveSerializers.FOR_MONGO.deserialize(test_case.serialized, type_hint) == test_case.value

        # Serialize and deserialize with type_name
        assert PrimitiveSerializers.FOR_MONGO.serialize(test_case.value, type_hint) == test_case.serialized
        assert PrimitiveSerializers.FOR_MONGO.deserialize(test_case.serialized, type_hint) == test_case.value

        # Test alternative serialized forms
        if test_case.alternative_serialized:
            for alternative_serialized in test_case.alternative_serialized:
                assert PrimitiveSerializers.FOR_MONGO.deserialize(alternative_serialized, type_hint) == test_case.value


def test_serialization_exceptions():
    """Test roundtrip serialization and deserialization."""

    test_cases = [
        # NoneType
        _TestCase(type_=NoneType, value=""),
        _TestCase(type_=NoneType, value="null"),
        # Bool
        _TestCase(type_=bool, value=0),
        _TestCase(type_=bool, value="None"),
        _TestCase(type_=bool, value="Null"),
        _TestCase(type_=int, value=2147483648),  # Out of range for int32
        _TestCase(type_=int, subtype="long", value=9007199254740992),  # Out of range for int54
        _TestCase(type_=type, value=str),  # Not a data, key or record class
    ]

    # Check exception cases with type name (without type name, the call will succeed for most values)
    for test_case in test_cases:

        # Get type hint from the test case
        type_hint = test_case.get_type_hint()

        # Test passthrough with type_name
        with pytest.raises(Exception):
            print(test_case.value)
            PrimitiveSerializers.PASSTHROUGH.serialize(test_case.value, type_hint)

        # Test default settings with type_name
        with pytest.raises(Exception):
            PrimitiveSerializers.DEFAULT.serialize(test_case.value, type_hint)


def test_deserialization_exceptions():
    """Test roundtrip serialization and deserialization."""

    test_cases = [
        # NoneType
        _TestCase(type_=NoneType, value=None, serialized="None"),
        # Bool
        _TestCase(type_=bool, value=None, serialized=0),
        _TestCase(type_=bool, value=None, serialized="None"),
        _TestCase(type_=bool, value=None, serialized="Null"),
        _TestCase(type_=bool, value=None, serialized="True"),
        _TestCase(type_=bool, value=None, serialized="False"),
        _TestCase(type_=bool, value=None, serialized="Y"),
        _TestCase(type_=bool, value=None, serialized="N"),
        _TestCase(type_=bool, value=None, serialized="YES"),
        _TestCase(type_=bool, value=None, serialized="NO"),  # Norway problem
        _TestCase(type_=int, value=None, serialized="2147483648"),  # Out of range for int32
        _TestCase(type_=int, value="long", serialized="9007199254740992"),  # Out of range for int54
    ]

    for test_case in test_cases:

        # Get type hint from the test case
        type_hint = test_case.get_type_hint()

        # Check exception cases
        with pytest.raises(Exception):
            PrimitiveSerializers.PASSTHROUGH.deserialize(test_case.serialized, type_hint)
        with pytest.raises(Exception):
            PrimitiveSerializers.DEFAULT.deserialize(test_case.serialized, type_hint)


if __name__ == "__main__":
    pytest.main([__file__])
