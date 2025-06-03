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
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.records.data_util import DataUtil
from cl.runtime.serializers.data_serializer import DataSerializer
from cl.runtime.serializers.enum_serializers import EnumSerializers
from cl.runtime.serializers.json_serializer import orjson_default
from cl.runtime.serializers.primitive_serializers import PrimitiveSerializers
from cl.runtime.serializers.type_inclusion import TypeInclusion
from stubs.cl.runtime import StubDataclassComposite
from stubs.cl.runtime import StubDataclassDoubleDerived
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassDictFields
from stubs.cl.runtime import StubDataclassDictListFields
from stubs.cl.runtime import StubDataclassListDictFields
from stubs.cl.runtime import StubDataclassListFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassOptionalFields
from stubs.cl.runtime import StubDataclassOtherDerived
from stubs.cl.runtime import StubDataclassPrimitiveFields
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassSingleton

_SAMPLE_TYPES = [
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
    # TODO: StubDataclassTupleFields,
]


def test_bidirectional():
    """Test DataSerializer.serialize method with bidirectional=True."""

    # Create the serializer
    serializer = DataSerializer(
        primitive_serializer=PrimitiveSerializers.PASSTHROUGH,
        enum_serializer=EnumSerializers.DEFAULT,
    ).build()

    for sample_type in _SAMPLE_TYPES:

        # Serialize to dict
        obj = sample_type().build()
        serialized = serializer.serialize(obj)

        # Deserialize and compare
        deserialized = serializer.deserialize(serialized)
        assert deserialized == DataUtil.remove_none(obj)

        # Convert serialized data to JSON using orjson to avoid relying on the functionality being tested
        result_str = orjson.dumps(
            serialized,
            option=orjson.OPT_INDENT_2 | orjson.OPT_OMIT_MICROSECONDS,
            default=orjson_default,
        ).decode()

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(sample_type.__name__)
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(result_str)

    RegressionGuard().verify_all()


def test_unidirectional():
    """Test DataSerializer.serialize method with bidirectional=None."""

    # Create the serializer
    serializer = DataSerializer(
        type_inclusion=TypeInclusion.OMIT,
        primitive_serializer=PrimitiveSerializers.PASSTHROUGH,
        enum_serializer=EnumSerializers.DEFAULT,
    ).build()

    for sample_type in _SAMPLE_TYPES:

        # Serialize to dict
        obj = sample_type().build()
        serialized = serializer.serialize(obj)

        # Convert to JSON using orjson
        result_str = orjson.dumps(
            serialized,
            option=orjson.OPT_INDENT_2 | orjson.OPT_OMIT_MICROSECONDS,
            default=orjson_default,
        ).decode()

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(sample_type.__name__)
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(result_str)

    RegressionGuard().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
