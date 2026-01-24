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
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.enum_serializers import EnumSerializers
from stubs.cl.runtime.records.enum.stub_int_enum import StubIntEnum


def test_serialize():
    """Test serialize method."""
    serializer = EnumSerializers.DEFAULT
    type_hint_required = TypeHint.for_type(StubIntEnum)
    type_hint_optional = TypeHint.for_type(StubIntEnum, optional=True)

    # Valid values without type
    assert serializer.serialize(None) is None
    assert serializer.serialize(StubIntEnum.ENUM_VALUE_1) == "EnumValue1"

    # Valid values with type
    assert serializer.serialize(None, type_hint_optional) is None
    assert serializer.serialize(StubIntEnum.ENUM_VALUE_1, type_hint_required) == "EnumValue1"
    assert serializer.serialize(StubIntEnum.ENUM_VALUE_1, type_hint_optional) == "EnumValue1"

    # Should raise
    with pytest.raises(Exception):
        serializer.serialize(1)  # noqa Numerical rather than string value
    with pytest.raises(Exception):
        serializer.serialize(None, type_hint_required)  # noqa None for required type hint


def test_deserialize():
    """Test deserialize method."""
    serializer = EnumSerializers.DEFAULT
    type_hint_required = TypeHint.for_type(StubIntEnum)
    type_hint_optional = TypeHint.for_type(StubIntEnum, optional=True)

    # Valid values
    assert serializer.deserialize(None, type_hint_optional) is None
    assert serializer.deserialize("EnumValue1", type_hint_required) == StubIntEnum.ENUM_VALUE_1
    assert serializer.deserialize("EnumValue1", type_hint_optional) == StubIntEnum.ENUM_VALUE_1

    # Should raise
    with pytest.raises(Exception):
        serializer.deserialize("EnumValue3", type_hint_required)  # Not a valid enum value
    with pytest.raises(Exception):
        serializer.deserialize(None, type_hint_required)  # None for required type hint
    with pytest.raises(Exception):
        serializer.deserialize("EnumValue1")  # noqa No type
    with pytest.raises(Exception):
        serializer.deserialize("ENUM_VALUE_1")  # noqa Not PascalCase


if __name__ == "__main__":
    pytest.main([__file__])
