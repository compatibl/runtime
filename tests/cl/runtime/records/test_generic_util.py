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
from cl.runtime.records.generic_util import GenericUtil
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import TKey
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime import StubDataclassRecordKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_concrete_record import StubDataclassConcreteRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived_generic_record import (
    StubDataclassDerivedGenericRecord,
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_arg import StubDataclassGenericArg
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_arg_1 import StubDataclassGenericArg1
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_record import StubDataclassGenericRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_record_key import StubDataclassGenericRecordKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_record_key import TKeyArg


def test_is_generic():
    """Test for GenericUtil.is_generic method."""

    # Immediate parent of a generic type, no generic params
    assert GenericUtil.is_generic(StubDataclassRecord)

    # Parent of parent of a generic type, no generic params
    assert GenericUtil.is_generic(StubDataclassNestedFields)

    # Generic alias with a concrete type argument
    assert GenericUtil.is_generic(StubDataclassGenericRecordKey[StubDataclassGenericArg1])

    # Generic type without a concrete type argument, should return TypeVar.__bound__
    assert GenericUtil.is_generic(StubDataclassGenericRecordKey)

    # Non-generic type
    assert not GenericUtil.is_generic(StubDataclassRecordKey)


def test_is_instance():
    """Test for GenericUtil.is_instance method."""

    # Parent of parent of a generic type, no generic params
    assert GenericUtil.is_instance(StubDataclassNestedFields(), StubDataclassNestedFields)

    # Generic alias with a concrete type argument
    assert GenericUtil.is_instance(
        StubDataclassGenericRecordKey(), StubDataclassGenericRecordKey[StubDataclassGenericArg1]
    )

    # Generic type without a concrete type argument, should return TypeVar.__bound__
    assert GenericUtil.is_instance(StubDataclassGenericRecordKey(), StubDataclassGenericRecordKey)

    # Non-generic type
    assert GenericUtil.is_instance(StubDataclassRecordKey(), StubDataclassRecordKey)


def test_get_bound_type():
    """Test for GenericUtil.get_bound_type method."""

    # Immediate parent of a generic type, no generic params
    assert GenericUtil.get_bound_type(StubDataclassRecord, TKey) == StubDataclassRecordKey

    # Parent of parent of a generic type, no generic params
    assert GenericUtil.get_bound_type(StubDataclassNestedFields, TKey) == StubDataclassRecordKey

    # Generic alias with a concrete type argument
    assert (
        GenericUtil.get_bound_type(StubDataclassGenericRecordKey[StubDataclassGenericArg1], TKeyArg)
        == StubDataclassGenericArg1
    )

    # Generic type without a concrete type argument, should return TypeVar.__bound__
    assert GenericUtil.get_bound_type(StubDataclassGenericRecordKey, TKeyArg) == KeyMixin

    # Error message when the class is not generic
    with pytest.raises(RuntimeError, match="no generic parameter"):
        GenericUtil.get_bound_type(StubDataclassRecordKey, TKey)

    # Error message when type var with this name is not found
    with pytest.raises(RuntimeError, match="no generic parameter"):
        GenericUtil.get_bound_type(StubDataclassGenericRecordKey, TKey)


def test_get_bound_type_dict():
    """Test for GenericUtil.get_bound_type_dict method."""

    # Immediate parent of a generic type, no generic params
    assert GenericUtil.get_bound_type_dict(StubDataclassRecord) == {"TKey": StubDataclassRecordKey}

    # Parent of parent of a generic type, no generic params
    assert GenericUtil.get_bound_type_dict(StubDataclassNestedFields) == {"TKey": StubDataclassRecordKey}

    # Full concrete type substitution, two params
    assert GenericUtil.get_bound_type_dict(StubDataclassConcreteRecord) == {
        "TKeyArg": StubDataclassRecordKey,
        "TRecordArg": StubDataclassGenericArg1,
        "TKey": StubDataclassGenericRecordKey[StubDataclassRecordKey],
    }

    # Partial concrete type substitution, two params
    assert GenericUtil.get_bound_type_dict(StubDataclassDerivedGenericRecord) == {
        "TKeyArg": StubDataclassRecordKey,
        "TRecordArg": StubDataclassGenericArg,
        "TKey": StubDataclassGenericRecordKey[StubDataclassRecordKey],
    }

    # No concrete type substitution, two params
    assert GenericUtil.get_bound_type_dict(StubDataclassGenericRecord) == {
        "TKeyArg": KeyMixin,
        "TRecordArg": StubDataclassGenericArg,
        "TKey": StubDataclassGenericRecordKey[KeyMixin],
    }

    # Generic alias with a concrete type argument
    assert GenericUtil.get_bound_type_dict(StubDataclassGenericRecordKey[StubDataclassGenericArg1]) == {
        "TKeyArg": StubDataclassGenericArg1
    }

    # Generic type without a concrete type argument, should return TKeyArg.__bound__
    assert GenericUtil.get_bound_type_dict(StubDataclassGenericRecordKey) == {"TKeyArg": TKeyArg.__bound__}

    # Not a generic class, the result is empty
    assert GenericUtil.get_bound_type_dict(StubDataclassRecordKey) == {}


if __name__ == "__main__":
    pytest.main([__file__])
