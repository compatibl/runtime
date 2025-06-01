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
from cl.runtime.records.protocols import TKey
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime import StubDataclassRecordKey
from stubs.cl.runtime.experiments.stub_binary_experiment import StubBinaryExperiment
from stubs.cl.runtime.experiments.stub_binary_experiment_key import StubBinaryExperimentKey
from stubs.cl.runtime.experiments.stub_binary_trial import StubBinaryTrial
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_arg import StubDataclassGenericArg
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_arg_1 import StubDataclassGenericArg1
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_record_key import StubDataclassGenericRecordKey, \
    TKeyArg


def test_get_concrete_type():
    """Test for GenericUtil.get_concrete_type method."""

    # Declared class
    assert GenericUtil.get_concrete_type(StubDataclassRecord, TKey) == StubDataclassRecordKey

    # Generic alias with concrete type argument
    assert GenericUtil.get_concrete_type(StubDataclassGenericRecordKey[StubDataclassGenericArg1], TKeyArg) == StubDataclassGenericArg1

    # Generic type without concrete type argument, should return the TypeVar bound parameter
    assert GenericUtil.get_concrete_type(StubDataclassGenericRecordKey, TKeyArg) == StubDataclassGenericArg

    # Error message when the class is not generic
    with pytest.raises(RuntimeError, match="no generic parameter"):
        GenericUtil.get_concrete_type(StubDataclassRecordKey, TKey)

    # Error message when type var with this name is not found
    with pytest.raises(RuntimeError, match="no generic parameter"):
        GenericUtil.get_concrete_type(StubDataclassGenericRecordKey, TKey)


def test_get_concrete_type_dict():
    """Test for GenericUtil.get_concrete_type_dict method."""

    # Immediate parent
    assert GenericUtil.get_concrete_type_dict(StubDataclassRecord) == {"TKey": StubDataclassRecordKey}

    # Parent of parent, non-generic
    assert GenericUtil.get_concrete_type_dict(StubDataclassNestedFields) == {"TKey": StubDataclassRecordKey}

    # Parent of parent, generic
    assert GenericUtil.get_concrete_type_dict(StubBinaryExperiment) == {
        "TKey": StubBinaryExperimentKey,
        "TTrial": StubBinaryTrial,
    }

    # Generic alias with concrete type argument
    assert GenericUtil.get_concrete_type_dict(StubDataclassGenericRecordKey[StubDataclassGenericArg1]) == {
        "TKeyArg": StubDataclassGenericArg1
    }

    # Generic type without concrete type argument, should return the TypeVar bound parameter
    assert GenericUtil.get_concrete_type_dict(StubDataclassGenericRecordKey) == {"TKeyArg": StubDataclassGenericArg}

    # Not a generic class, the result is empty
    assert GenericUtil.get_concrete_type_dict(StubDataclassRecordKey) == {}


if __name__ == "__main__":
    pytest.main([__file__])
