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
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.ui_dict_serializer import UiDictSerializer
from cl.runtime.serializers.yaml_serializers import YamlSerializers
from stubs.cl.runtime import StubDataclassComposite
from stubs.cl.runtime import StubDataclassDerivedFromDerivedRecord
from stubs.cl.runtime import StubDataclassDerivedRecord
from stubs.cl.runtime import StubDataclassListFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassOptionalFields
from stubs.cl.runtime import StubDataclassOtherDerivedRecord
from stubs.cl.runtime import StubDataclassPrimitiveFields
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime import StubDataclassSingleton


def test_data_serialization():
    sample_types = [
        StubDataclassRecord,
        StubDataclassNestedFields,
        StubDataclassComposite,
        StubDataclassDerivedRecord,
        StubDataclassDerivedFromDerivedRecord,
        StubDataclassOtherDerivedRecord,
        StubDataclassListFields,
        # StubDataclassTupleFields,
        StubDataclassOptionalFields,
        # TODO (Roman): Uncomment when serialization format supports all dict value types
        # StubDataclassDictFields,
        # StubDataclassDictListFields,
        # StubDataclassListDictFields,
        StubDataclassPrimitiveFields,
        StubDataclassSingleton,
        # StubDataclassAnyFields,  TODO (Roman): Uncomment when supported consistent Any ui serialization.
    ]

    serializer_old = UiDictSerializer()

    for sample_type in sample_types:
        sample = sample_type()
        serialized = DataSerializers.FOR_UI.serialize(sample)
        deserialized = DataSerializers.FOR_UI.deserialize(serialized)
        assert deserialized == sample

        serialized_old = serializer_old.serialize_data(sample)
        assert serialized_old == serialized

        deserialized_old = serializer_old.deserialize_data(serialized_old)
        assert deserialized_old == deserialized

        # Record in RegressionGuard
        result_str = YamlSerializers.REPORTING.serialize(serialized)
        guard = RegressionGuard(channel=sample_type.__name__)
        guard.write(result_str)
    RegressionGuard().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
