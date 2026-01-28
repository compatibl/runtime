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
from cl.runtime.records.builder_checks import BuilderChecks
from cl.runtime.records.protocols import is_data_key_or_record_type
from cl.runtime.records.protocols import is_key_or_record_type
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.key_serializers import KeySerializers
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_composite_key import StubDataclassCompositeKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_base_key import StubDataclassPolymorphicBaseKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_composite_key import (
    StubDataclassPolymorphicCompositeKey,
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_key import StubDataclassPolymorphicKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields_key import StubDataclassPrimitiveFieldsKey

_SERIALIZATION_SAMPLES = [
    StubDataclassKey().build(),
    StubDataclassCompositeKey().build(),
    StubDataclassPrimitiveFieldsKey().build(),
    StubDataclassPolymorphicKey().build(),
]

_SERIALIZATION_EXCEPTION_SAMPLES = [
    str,  # Primitive type
    float,  # Primitive type
    [StubDataclassKey().build()],  # List type
    {"a": StubDataclassKey().build()},  # Dict type
]


def test_serialization():  # TODO: Rename to test_delimited
    """Test KeySerializer.serialize method."""

    for sample in _SERIALIZATION_SAMPLES:
        # Roundtrip serialization
        serialized = KeySerializers.DELIMITED.serialize(sample)
        type_hint = TypeHint.for_type(sample.__class__)
        deserialized = KeySerializers.DELIMITED.deserialize(serialized, type_hint)
        assert BuilderChecks.is_equal(sample, deserialized)

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(typename(type(sample)))
        guard = RegressionGuard(prefix=snake_case_type_name).build()
        guard.write(serialized)
    RegressionGuard.verify_all()


def test_polymorphic():
    """Test KeySerializer.serialize method with polymorphic key."""

    # Ensure base key is treated as key
    assert is_key_type(StubDataclassPolymorphicBaseKey)
    assert is_key_or_record_type(StubDataclassPolymorphicBaseKey)
    assert is_data_key_or_record_type(StubDataclassPolymorphicBaseKey)

    # Ensure derived key is treated as key
    assert is_key_type(StubDataclassPolymorphicKey)
    assert is_key_or_record_type(StubDataclassPolymorphicKey)
    assert is_data_key_or_record_type(StubDataclassPolymorphicKey)

    # Sample for derived and type hint for base
    sample = StubDataclassPolymorphicKey().build()
    base_type = StubDataclassPolymorphicBaseKey
    base_type_hint = TypeHint.for_type(base_type)

    # Roundtrip serialization
    serialized = KeySerializers.DELIMITED.serialize(sample, base_type_hint)
    assert serialized == f"{typename(type(sample))};{sample.id}"
    deserialized = KeySerializers.DELIMITED.deserialize(serialized, base_type_hint)
    assert BuilderChecks.is_equal(sample, deserialized)

    # return  # TODO: Restore after composite key is supported

    # Sample for derived and type hint for base
    composite_key = StubDataclassPolymorphicCompositeKey(
        base_key_field=StubDataclassPolymorphicKey(id="abc"),
        root_key_field=StubDataclassPolymorphicKey(id="def"),
    ).build()
    composite_key_hint = TypeHint.for_type(StubDataclassPolymorphicCompositeKey)

    # Roundtrip serialization
    serialized = KeySerializers.DELIMITED.serialize(composite_key, composite_key_hint)
    inner_type = typename(StubDataclassPolymorphicKey)
    assert serialized == (
        f"{inner_type};{composite_key.base_key_field.id};" f"{inner_type};{composite_key.root_key_field.id}"
    )  # noqa
    deserialized = KeySerializers.DELIMITED.deserialize(serialized, composite_key_hint)
    assert BuilderChecks.is_equal(composite_key, deserialized)


def test_for_sqlite():
    """Test KeySerializer.serialize method."""

    for sample in _SERIALIZATION_SAMPLES:
        # Roundtrip serialization
        serialized = KeySerializers.FOR_SQLITE.serialize(sample)
        type_hint = TypeHint.for_type(sample.__class__)
        deserialized = KeySerializers.FOR_SQLITE.deserialize(serialized, type_hint)
        assert BuilderChecks.is_equal(sample, deserialized)

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(typename(type(sample)))
        guard = RegressionGuard(prefix=snake_case_type_name).build()
        guard.write(serialized)
    RegressionGuard.verify_all()


def test_serialization_exceptions():
    """Test exception handling in KeySerializer.serialize method."""

    for sample in _SERIALIZATION_EXCEPTION_SAMPLES:
        with pytest.raises(RuntimeError):
            KeySerializers.DELIMITED.serialize(sample)


if __name__ == "__main__":
    pytest.main([__file__])
