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
from cl.runtime.qa.pytest.pytest_util import PytestUtil
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.serializers.primitive_serializers import PrimitiveSerializers
from cl.runtime.serializers.yaml_serializers import YamlSerializers
from stubs.cl.runtime import StubDataclassCompositeKey
from stubs.cl.runtime import StubDataclassRecordKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields_key import StubDataclassPrimitiveFieldsKey

_SERIALIZATION_SAMPLES = [
    # StubDataclassRecordKey().build(),
    StubDataclassCompositeKey().build(),
    StubDataclassPrimitiveFieldsKey().build(),
]

_SERIALIZATION_EXCEPTION_SAMPLES = [
    str,  # Primitive type
    float,  # Primitive type
    [StubDataclassRecordKey().build()],  # List type
    {"a": StubDataclassRecordKey().build()},  # Dict type
]


def test_serialization():  # TODO: Rename to test_delimited
    """Test KeySerializer.serialize method."""

    for sample in _SERIALIZATION_SAMPLES:
        # Roundtrip serialization
        serialized = KeySerializers.DELIMITED.serialize(sample)
        deserialized = KeySerializers.DELIMITED.deserialize(serialized, type(sample))
        assert sample == PytestUtil.approx(deserialized)

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(TypeUtil.name(sample))
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(serialized)
    RegressionGuard().verify_all()


def test_for_sqlite():
    """Test KeySerializer.serialize method."""

    for sample in _SERIALIZATION_SAMPLES:
        # Roundtrip serialization
        serialized = KeySerializers.FOR_SQLITE.serialize(sample)
        deserialized = KeySerializers.FOR_SQLITE.deserialize(serialized, type(sample))
        assert sample == PytestUtil.approx(deserialized)

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(TypeUtil.name(sample))
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(serialized)
    RegressionGuard().verify_all()


def test_serialization_exceptions():
    """Test exception handling in KeySerializer.serialize method."""

    for sample in _SERIALIZATION_EXCEPTION_SAMPLES:
        # Attempt serialization
        with pytest.raises(RuntimeError):
            print(f"Serializing type {type(sample)}")
            KeySerializers.DELIMITED.serialize(sample)


if __name__ == "__main__":
    pytest.main([__file__])
