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
from cl.runtime.records.builder_checks import BuilderChecks
from cl.runtime.serializers.data_serializer import DataSerializer
from cl.runtime.serializers.enum_serializers import EnumSerializers
from cl.runtime.serializers.primitive_serializers import PrimitiveSerializers
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_composite import StubDataclassComposite
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dict_fields import StubDataclassDictFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dict_list_fields import StubDataclassDictListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_double_derived import StubDataclassDoubleDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_dict_fields import StubDataclassListDictFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import StubDataclassListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_optional_fields import StubDataclassOptionalFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_other_derived import StubDataclassOtherDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields import StubDataclassPrimitiveFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_singleton import StubDataclassSingleton


def test_passthrough():
    """Test coroutine for /schema/typeV2 route."""

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
        StubDataclassSingleton,
        # TODO: StubDataclassAnyFields,
        # TODO: StubDataclassTupleFields,
        # TODO: Support serialization of classes with cyclic references
    ]

    serializer = DataSerializer(
        primitive_serializer=PrimitiveSerializers.PASSTHROUGH,
        enum_serializer=EnumSerializers.DEFAULT,
    ).build()

    for sample_type in sample_types:
        obj_1 = sample_type().build()
        serialized_1 = serializer.serialize(obj_1)
        obj_2 = serializer.deserialize(serialized_1).build()
        serialized_2 = serializer.serialize(obj_2)

        assert BuilderChecks.is_equal(obj_1, obj_2)
        assert serialized_1 == serialized_2


if __name__ == "__main__":
    pytest.main([__file__])
