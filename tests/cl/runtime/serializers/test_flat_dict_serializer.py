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
import json
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.flat_dict_serializer import FlatDictSerializer
from cl.runtime.serializers.yaml_serializers import YamlSerializers
from stubs.cl.runtime import StubDataclassComposite
from stubs.cl.runtime import StubDataclassDerivedFromDerivedRecord
from stubs.cl.runtime import StubDataclassDerivedRecord
from stubs.cl.runtime import StubDataclassDictFields
from stubs.cl.runtime import StubDataclassDictListFields
from stubs.cl.runtime import StubDataclassListDictFields
from stubs.cl.runtime import StubDataclassListFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassOptionalFields
from stubs.cl.runtime import StubDataclassOtherDerivedRecord
from stubs.cl.runtime import StubDataclassPrimitiveFields


def test_data_serialization():
    sample_types = [
        # StubDataclassRecord,
        StubDataclassNestedFields,
        StubDataclassComposite,
        StubDataclassDerivedRecord,
        StubDataclassDerivedFromDerivedRecord,
        StubDataclassOtherDerivedRecord,
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

    serializer_old = FlatDictSerializer()

    for sample_type in sample_types:
        sample = sample_type()
        serialized = DataSerializers.FOR_SQLITE.serialize(sample)
        # deserialized = DataSerializers.FOR_UI.deserialize(serialized)
        # TODO: assert deserialized == sample

        serialized_old = serializer_old.serialize_data(sample)
        # assert serialized_old == serialized

        deserialized_old = serializer_old.deserialize_data(serialized_old)
        # assert deserialized_old == sample

        # Read JSONN and

        # Record in RegressionGuard
        resuld_dict_old = json.loads(serialized_old)
        result_str_old = YamlSerializers.FOR_REPORTING.serialize(resuld_dict_old)
        guard = RegressionGuard(channel=f"{sample_type.__name__}")
        guard.write(serialized)

        # guard = RegressionGuard(channel=sample_type.__name__)
        # guard.write(serialized)
    RegressionGuard().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
