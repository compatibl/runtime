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
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.primitive_serializers import PrimitiveSerializers
from cl.runtime.primitive.time_util import TimeUtil

def test_passthrough():
    """Test serialize method when all primitive types are passed through."""

    # Pass through all primitive types
    serializer = PrimitiveSerializers.PASSTHROUGH

    # None
    assert serializer.serialize(None) is None

    # String
    assert serializer.serialize("") is None  # Empty string is serialized as None
    assert serializer.serialize("abc") == "abc"

    # Int
    assert serializer.serialize(123) == 123

    # Float
    assert serializer.serialize(1.0) == 1.0

    # Date
    date_value = dt.date(2023, 4, 21)
    assert serializer.serialize(date_value) == date_value

    # Time
    time_value = TimeUtil.from_fields(11, 10, 0)
    assert serializer.serialize(time_value) == time_value

    # Datetime
    datetime_value = DatetimeUtil.from_fields(2023, 4, 21, 11, 10, 0)
    assert serializer.serialize(datetime_value) == datetime_value

    # TODO: Add tests for UUID and bytes
    # TODO: Add tests for subtypes


def test_default():
    """Test serialize method when all primitive types except None use default serialiation to string."""

    # Serialize all primitive types except None to string using default format, pass through None
    serializer = PrimitiveSerializers.DEFAULT

    # None
    assert serializer.serialize(None) is None

    # String
    assert serializer.serialize("") is None  # Empty string is serialized as None
    assert serializer.serialize("abc") == "abc"

    # Int
    assert serializer.serialize(123) == "123"
    assert serializer.serialize(-123) == "-123"

    # Float
    assert serializer.serialize(1.0) == "1."
    assert serializer.serialize(-1.23) == "-1.23"

    # Date
    assert serializer.serialize(dt.date(2023, 4, 21)) == "2023-04-21"

    # Time
    value = TimeUtil.from_fields(11, 10, 0)
    assert serializer.serialize(value) == "11:10:00.000"
    value = TimeUtil.from_fields(11, 10, 0, millisecond=123)
    assert serializer.serialize(value) == "11:10:00.123"

    # Datetime
    value = DatetimeUtil.from_fields(2023, 4, 21, 11, 10, 0)
    assert serializer.serialize(value) == "2023-04-21T11:10:00.000Z"
    value = DatetimeUtil.from_fields(2023, 4, 21, 11, 10, 0, millisecond=123)
    assert serializer.serialize(value) == "2023-04-21T11:10:00.123Z"

    # TODO: Add tests for UUID and bytes
    # TODO: Add tests for subtypes


if __name__ == "__main__":
    pytest.main([__file__])
