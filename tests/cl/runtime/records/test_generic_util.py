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
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassKey
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_bound_generic import StubDataclassBoundGeneric
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_bound_generic_key import StubDataclassBoundGenericKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived_generic import StubDataclassDerivedGeneric
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic import StubDataclassGeneric
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_arg import StubDataclassGenericArg
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_arg_1 import StubDataclassGenericArg1
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_arg_2 import StubDataclassGenericArg2
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_key import StubDataclassGenericKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_key import TKeyArg


def test_is_generic():
    """Test for GenericUtil.is_generic method."""

    # Immediate parent of a generic type, no generic params
    assert GenericUtil.is_generic(StubDataclass)

    # Parent of parent of a generic type, no generic params
    assert GenericUtil.is_generic(StubDataclassNestedFields)

    # Generic alias with a concrete type argument
    assert GenericUtil.is_generic(StubDataclassGenericKey[StubDataclassGenericArg1])

    # Generic type without a concrete type argument, should return TypeVar.__bound__
    assert GenericUtil.is_generic(StubDataclassGenericKey)

    # Non-generic type
    assert not GenericUtil.is_generic(StubDataclassKey)


def test_is_instance():
    """Test for GenericUtil.is_instance method."""

    # Parent of parent of a generic type, no generic params
    assert GenericUtil.is_instance(StubDataclassNestedFields(), StubDataclassNestedFields)

    # Generic alias with a concrete type argument
    assert GenericUtil.is_instance(StubDataclassBoundGenericKey(), StubDataclassGenericKey[StubDataclassGenericArg1])

    # Generic type without a concrete type argument, should return TypeVar.__bound__
    assert GenericUtil.is_instance(StubDataclassBoundGenericKey(), StubDataclassGenericKey)

    # Non-generic type
    assert GenericUtil.is_instance(StubDataclassKey(), StubDataclassKey)


def test_get_bound_type():
    """Test for GenericUtil.get_bound_type method."""

    # Immediate parent of a generic type, no generic params
    assert GenericUtil.get_bound_type(StubDataclass, TKey) == StubDataclassKey

    # Parent of parent of a generic type, no generic params
    assert GenericUtil.get_bound_type(StubDataclassNestedFields, TKey) == StubDataclassKey

    # Generic alias with a concrete type argument
    assert (
        GenericUtil.get_bound_type(StubDataclassGenericKey[StubDataclassGenericArg1], TKeyArg)
        == StubDataclassGenericArg1
    )

    # Generic type without a concrete type argument, should return TypeVar.__bound__
    assert GenericUtil.get_bound_type(StubDataclassGenericKey, TKeyArg) == KeyMixin

    # Error message when the class is not generic
    with pytest.raises(RuntimeError, match="no generic parameter"):
        GenericUtil.get_bound_type(StubDataclassKey, TKey)

    # Error message when type var with this name is not found
    with pytest.raises(RuntimeError, match="no generic parameter"):
        GenericUtil.get_bound_type(StubDataclassGenericKey, TKey)


def test_get_bound_type_dict():
    """Test for GenericUtil.get_bound_type_dict method."""

    # Immediate parent of a generic type, no generic params
    assert GenericUtil.get_bound_type_dict(StubDataclass) == {"TKey": StubDataclassKey}

    # Parent of parent of a generic type, no generic params
    assert GenericUtil.get_bound_type_dict(StubDataclassNestedFields) == {"TKey": StubDataclassKey}

    # Full concrete type substitution, two params
    assert GenericUtil.get_bound_type_dict(StubDataclassBoundGeneric) == {
        "TKeyArg": StubDataclassKey,
        "TRecordArg1": StubDataclassGenericArg1,
        "TRecordArg2": StubDataclassGenericArg2,
        "TKey": StubDataclassBoundGenericKey,
    }

    # Partial concrete type substitution, two params
    assert GenericUtil.get_bound_type_dict(StubDataclassDerivedGeneric) == {
        "TKeyArg": StubDataclassKey,
        "TRecordArg1": StubDataclassGenericArg,
        "TRecordArg2": StubDataclassGenericArg2,
        "TKey": StubDataclassBoundGenericKey,
    }

    # No concrete type substitution, two params
    assert GenericUtil.get_bound_type_dict(StubDataclassGeneric) == {
        "TKeyArg": StubDataclassKey,
        "TRecordArg1": StubDataclassGenericArg,
        "TRecordArg2": StubDataclassGenericArg,
        "TKey": StubDataclassBoundGenericKey,
    }

    # Generic alias with a concrete type argument
    assert GenericUtil.get_bound_type_dict(StubDataclassGenericKey[StubDataclassKey]) == {
        "TKeyArg": StubDataclassKey
    }

    # Generic type without a concrete type argument, should return TKeyArg.__bound__
    assert GenericUtil.get_bound_type_dict(StubDataclassGenericKey) == {"TKeyArg": TKeyArg.__bound__}

    # Not a generic class, the result is empty
    assert GenericUtil.get_bound_type_dict(StubDataclassKey) == {}


if __name__ == "__main__":
    pytest.main([__file__])
