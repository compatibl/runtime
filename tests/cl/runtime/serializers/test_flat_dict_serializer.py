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
from cl.runtime.qa.pytest.pytest_util import PytestUtil
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.records.mapping_util import MappingUtil
from cl.runtime.records.freeze_util import FreezeUtil
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.data_serializers import DataSerializers
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassComposite
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassDictFields
from stubs.cl.runtime import StubDataclassDictListFields
from stubs.cl.runtime import StubDataclassDoubleDerived
from stubs.cl.runtime import StubDataclassListDictFields
from stubs.cl.runtime import StubDataclassListFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassOptionalFields
from stubs.cl.runtime import StubDataclassOtherDerived
from stubs.cl.runtime import StubDataclassPrimitiveFields


def test_data_serialization():
    sample_types = [
        StubDataclass,
        StubDataclassNestedFields,
        StubDataclassComposite,
        StubDataclassDerived,
        StubDataclassDoubleDerived,
        StubDataclassOtherDerived,
        StubDataclassListFields,
        StubDataclassOptionalFields,
        StubDataclassDictFields,
        StubDataclassDictListFields,
        StubDataclassListDictFields,
        StubDataclassPrimitiveFields,
        # TODO: StubDataclassSingleton, # TODO: Investigate why this is failing
        # TODO: StubDataclassAnyFields,
        # TODO: StubDataclassTupleFields,
    ]

    for sample_type in sample_types:
        sample = sample_type().build()
        type_hint = TypeHint.for_class(sample_type)
        serialized = DataSerializers.FOR_SQLITE.serialize(sample)
        deserialized = DataSerializers.FOR_SQLITE.deserialize(serialized, type_hint)
        assert deserialized == PytestUtil.approx(FreezeUtil.freeze(MappingUtil.remove_none(sample)))

        # Record in RegressionGuard
        guard = RegressionGuard(channel=f"{sample_type.__name__}")
        guard.write(serialized)
    RegressionGuard().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
