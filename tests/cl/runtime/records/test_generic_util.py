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
from frozendict import frozendict
from cl.runtime import RecordMixin
from cl.runtime.experiments.experiment_mixin import ExperimentMixin
from cl.runtime.records.generic_util import GenericUtil
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime import StubDataclassRecordKey
from stubs.cl.runtime.experiments.stub_binary_experiment import StubBinaryExperiment
from stubs.cl.runtime.experiments.stub_binary_experiment_key import StubBinaryExperimentKey
from stubs.cl.runtime.experiments.stub_binary_trial import StubBinaryTrial


def test_get_generic_args():
    """Test for GenericUtil.get_generic_args method."""

    # Immediate parent
    assert GenericUtil.get_generic_args(StubDataclassRecord, RecordMixin) == frozendict(
        {
            "TKey": StubDataclassRecordKey,
        }
    )

    # Parent of parent, non-generic
    assert GenericUtil.get_generic_args(StubDataclassNestedFields, RecordMixin) == frozendict(
        {
            "TKey": StubDataclassRecordKey,
        }
    )

    # Parent of parent, generic
    assert GenericUtil.get_generic_args(StubBinaryExperiment, ExperimentMixin) == frozendict(
        {
            "TKey": StubBinaryExperimentKey,
            "TTrial": StubBinaryTrial,
        }
    )

    # Generic base is not found
    with pytest.raises(RuntimeError, match="is not a base class of"):
        GenericUtil.get_generic_args(StubDataclassRecordKey, RecordMixin)

    # Second parameter is not a generic class
    with pytest.raises(RuntimeError, match="is not generic"):
        GenericUtil.get_generic_args(StubDataclassRecord, StubDataclassRecordKey)


if __name__ == "__main__":
    pytest.main([__file__])
