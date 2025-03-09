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
from cl.runtime.primitive.time_util import TimeUtil
from cl.runtime.serializers.primitive_serializer import PrimitiveSerializer



def test_serialize():
    """Test serialize method."""

    serializer = PrimitiveSerializer().build()

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
