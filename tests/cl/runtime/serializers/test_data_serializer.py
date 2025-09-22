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
import orjson
from frozendict import frozendict
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.records.builder_checks import BuilderChecks
from cl.runtime.serializers.data_serializer import DataSerializer
from cl.runtime.serializers.enum_serializers import EnumSerializers
from cl.runtime.serializers.json_serializer import orjson_default
from cl.runtime.serializers.primitive_serializers import PrimitiveSerializers
from cl.runtime.serializers.type_inclusion import TypeInclusion
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
from stubs.cl.runtime import StubDataclassSingleton
from stubs.cl.runtime import StubDataclassTupleFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_empty_fields import StubDataclassEmptyFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_frozendict_fields import StubDataclassFrozendictFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_numpy_fields import StubDataclassNumpyFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic import StubDataclassPolymorphic
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_composite import (
    StubDataclassPolymorphicComposite,
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_key import StubDataclassPolymorphicKey
from stubs.cl.runtime.records.for_pydantic.stub_pydantic import StubPydantic

_SAMPLES = [
    StubDataclass(),
    StubDataclassNestedFields(),
    StubDataclassComposite(),
    StubDataclassDerived(),
    StubDataclassDoubleDerived(),
    StubDataclassOtherDerived(),
    StubDataclassTupleFields(),
    StubDataclassListFields(),
    StubDataclassOptionalFields(),
    StubDataclassFrozendictFields(),
    StubDataclassDictFields(),
    StubDataclassDictListFields(),
    StubDataclassListDictFields(),
    StubDataclassPrimitiveFields(),
    StubDataclassSingleton(),
    StubDataclassPolymorphic(
        base_key_field=StubDataclassPolymorphicKey(),
        root_key_field=StubDataclassPolymorphicKey(),
        record_as_base_key_field=StubDataclassPolymorphic(),
        record_as_root_key_field=StubDataclassPolymorphic(),
    ),
    StubDataclassPolymorphicComposite(
        base_key_field=StubDataclassPolymorphicKey(),
        root_key_field=StubDataclassPolymorphicKey(),
    ),
    StubDataclassNumpyFields(),
    StubDataclassEmptyFields(),  # Fields set to None
    StubDataclassEmptyFields(  # Fields set to empty mutable containers
        empty_str="",
        empty_list=[],
        empty_tuple=[],  # noqa
        empty_dict={},
        empty_frozendict={},  # noqa
    ),
    StubDataclassEmptyFields(  # Fields set to empty immutable containers
        empty_str="",
        empty_list=(),  # noqa
        empty_tuple=(),
        empty_dict=frozendict(),
        empty_frozendict=frozendict(),
    ),
    StubDataclassEmptyFields(  # Fields set to non-empty mutable containers
        empty_str="",
        empty_list=["abc"],
        empty_tuple=["abc"],  # noqa
        empty_dict={"1": "abc"},
        empty_frozendict={"1": "abc"},  # noqa
    ),
    StubDataclassEmptyFields(  # Fields set to non-empty immutable containers
        empty_str="",
        empty_list=("abc",),  # noqa
        empty_tuple=("abc",),
        empty_dict=frozendict({"1": "abc"}),
        empty_frozendict=frozendict({"1": "abc"}),
    ),
    StubPydantic(),
]


_INVALID_SAMPLES = [
    # TODO (Roman): The Stub class must be valid for displaying on UI. Create a separate class for testing invalid fields.
    # (
    #     StubDataclassNumpyFields(untyped_ndarray=np.array([1.0, 2.0])),
    #     "is an ndarray but does not specify dtype",
    # ),  # noqa
]


def test_bidirectional():
    """Test DataSerializer.serialize method with bidirectional=True."""

    # Create the serializer
    serializer = DataSerializer(
        primitive_serializer=PrimitiveSerializers.PASSTHROUGH,
        enum_serializer=EnumSerializers.DEFAULT,
    ).build()

    for sample in _SAMPLES:
        sample = sample.build()

        # Serialize to dict
        serialized = serializer.serialize(sample)

        # Deserialize and compare
        deserialized = serializer.deserialize(serialized)
        assert BuilderChecks.is_equal(deserialized, sample)

        # Convert serialized data to JSON using orjson to avoid relying on the functionality being tested
        result_str = orjson.dumps(
            serialized,
            option=orjson.OPT_INDENT_2 | orjson.OPT_OMIT_MICROSECONDS,
            default=orjson_default,
        ).decode()

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(type(sample).__name__)
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(result_str)

    RegressionGuard().verify_all()

    for sample, match in _INVALID_SAMPLES:
        with pytest.raises(Exception, match=match):
            sample = sample.build()
            serializer.serialize(sample)


def test_unidirectional():
    """Test DataSerializer.serialize method with bidirectional=None."""

    # Create the serializer
    serializer = DataSerializer(
        type_inclusion=TypeInclusion.OMIT,
        primitive_serializer=PrimitiveSerializers.PASSTHROUGH,
        enum_serializer=EnumSerializers.DEFAULT,
    ).build()

    for sample in _SAMPLES:
        sample = sample.build()

        # Serialize to dict
        serialized = serializer.serialize(sample)

        # Convert to JSON using orjson
        result_str = orjson.dumps(
            serialized,
            option=orjson.OPT_INDENT_2 | orjson.OPT_OMIT_MICROSECONDS,
            default=orjson_default,
        ).decode()

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(type(sample).__name__)
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(result_str)

    RegressionGuard().verify_all()

    for sample, match in _INVALID_SAMPLES:
        with pytest.raises(Exception, match=match):
            sample = sample.build()
            serializer.serialize(sample)


if __name__ == "__main__":
    pytest.main([__file__])
