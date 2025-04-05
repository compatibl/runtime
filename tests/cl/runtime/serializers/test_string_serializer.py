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
from cl.runtime.serializers.key_serializers import KeySerializers
from stubs.cl.runtime import StubDataclassComposite
from stubs.cl.runtime import StubDataclassListFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassOptionalFields
from stubs.cl.runtime import StubDataclassPrimitiveFields
from stubs.cl.runtime import StubDataclassRecord

_KEY_SERIALIZER = KeySerializers.DELIMITED


def test_key_serialization():
    """Test key serialization."""

    sample_types = [
        StubDataclassRecord,
        StubDataclassPrimitiveFields,
        StubDataclassListFields,
        StubDataclassNestedFields,
        StubDataclassComposite,
        StubDataclassOptionalFields,
    ]

    for sample_type in sample_types:
        obj_1 = sample_type()
        obj_1_key = obj_1.get_key()
        serialized = _KEY_SERIALIZER.serialize(obj_1_key)

        type_hint = TypeHint.for_class(sample_type.get_key_type())
        deserialized_key = _KEY_SERIALIZER.deserialize(serialized, type_hint).build()
        assert obj_1_key == deserialized_key


if __name__ == "__main__":
    pytest.main([__file__])
