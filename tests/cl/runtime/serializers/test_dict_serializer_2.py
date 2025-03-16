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
from cl.runtime.serializers.dict_serializer_2 import DictSerializer2
from cl.runtime.serializers.json_serializer import orjson_default
from cl.runtime.testing.regression_guard import RegressionGuard
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
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime import StubDataclassSingleton
from stubs.cl.runtime import StubDataclassTupleFields

_SAMPLE_TYPES = [
    StubDataclassRecord,
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
    StubDataclassSingleton,
    StubDataclassTupleFields,
]


def test_to_dict():
    """Test DictSerializer2.to_dict method."""

    # Create the serializer
    serializer = DictSerializer2().build()

    for sample_type in _SAMPLE_TYPES:

        # Serialize to dict
        obj = sample_type().build()
        obj_dict = serializer.serialize(obj)

        # Convert to JSON using orjson
        result_str = orjson.dumps(
            obj_dict,
            option=orjson.OPT_INDENT_2 | orjson.OPT_OMIT_MICROSECONDS,
            default=orjson_default,
        ).decode()

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(sample_type.__name__)
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(result_str)

    RegressionGuard().verify_all()


def test_to_dict_omit_type():
    """Test DictSerializer2.to_dict method with omit_type=True."""

    # Create the serializer
    serializer = DictSerializer2(omit_type=True).build()

    for sample_type in _SAMPLE_TYPES:

        # Serialize to dict
        obj = sample_type().build()
        obj_dict = serializer.serialize(obj)

        # Convert to JSON using orjson
        result_str = orjson.dumps(
            obj_dict,
            option=orjson.OPT_INDENT_2 | orjson.OPT_OMIT_MICROSECONDS,
            default=orjson_default,
        ).decode()

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(sample_type.__name__)
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(result_str)

    RegressionGuard().verify_all()


def _test_from_dict():
    """Test DictSerializer2.from_dict method with omit_type flag set."""

    # Create the serializer with omit_type flag
    serializer = DictSerializer2().build()

    for sample_type in _SAMPLE_TYPES:

        # Roundtrip serialization test
        obj = sample_type().build()
        serialized = serializer.serialize(obj, sample_type)
        deserialized = serializer.deserialize(serialized, sample_type)
        assert obj == deserialized


def test_from_dict_omit_type():
    """Test DictSerializer2.from_dict method with omit_type flag set."""

    # Create the serializer with omit_type flag
    serializer = DictSerializer2(omit_type=True).build()

    for sample_type in _SAMPLE_TYPES:

        # Roundtrip serialization test
        obj = sample_type().build()
        obj_dict = serializer.serialize(obj)
        obj_from_dict = serializer.deserialize(obj_dict)
        assert obj_dict == obj_from_dict


if __name__ == "__main__":
    pytest.main([__file__])
