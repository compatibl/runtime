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
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.key_serializer import KeySerializer
from stubs.cl.runtime import StubDataclassCompositeKey, StubDataclassListFields, StubDataclassDictFields
from stubs.cl.runtime import StubDataclassRecordKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields_key import StubDataclassPrimitiveFieldsKey

_SERIALIZATION_SAMPLES = [
    StubDataclassRecordKey().build(),
    StubDataclassCompositeKey().build(),
    StubDataclassPrimitiveFieldsKey().build(),
]

_SERIALIZATION_EXCEPTION_SAMPLES = [
    str,  # Primitive type
    float,  # Primitive type
    StubDataclassRecordKey(),  # Did not invoke build
    [StubDataclassRecordKey().build()],  # List type
    {"a": StubDataclassRecordKey().build()},  # Dict type
    StubDataclassListFields().build(),  # Sequence fields
    StubDataclassDictFields().build(),  # Mapping fields
]


def test_serialization():
    """Test KeySerializer.serialize method."""

    # Create the serializer
    serializer = KeySerializer().build()

    for sample in _SERIALIZATION_SAMPLES:
        # Serialize without type information
        untyped_serialized = serializer.serialize(sample)
        untyped_delimited = ";".join(untyped_serialized)

        # Serialize with type information, output should be the same
        typed_serialized = serializer.serialize(sample, (sample.__class__.__name__,))
        assert typed_serialized == untyped_serialized

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(TypeUtil.name(sample))
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(untyped_delimited)
    RegressionGuard().verify_all()


def test_serialization_exceptions():
    """Test exception handling in KeySerializer.serialize method."""

    # Create the serializer
    serializer = KeySerializer().build()

    for sample in _SERIALIZATION_EXCEPTION_SAMPLES:
        # Attempt untyped serialization
        with pytest.raises(RuntimeError):
            serializer.serialize(sample)
        # Attempt typed serialization
        with pytest.raises(RuntimeError):
            serializer.serialize(sample, (sample.__class__.__name__,))


if __name__ == "__main__":
    pytest.main([__file__])
