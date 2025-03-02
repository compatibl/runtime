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
import orjson
import pytest

from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.serialization.dict_serializer import DictSerializer
from cl.runtime.serialization.one_way_serializer import OneWaySerializer
from cl.runtime.testing.regression_guard import RegressionGuard
from stubs.cl.runtime import StubDataclassAnyFields
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


def orjson_default(obj):
    """Handler for unsupported types in orjson."""
    if isinstance(obj, bytes):
        return obj.hex()  # Convert bytes to string using hex encoding
    raise RuntimeError(f"Object of type {obj.__class__.__name__} is not JSON serializable.")


def test_to_dict():
    """Test OneWaySerializer.to_dict method serialize_primitive flag."""

    serializer = OneWaySerializer()

    for sample_type in _SAMPLE_TYPES:
        obj = sample_type().build()
        obj_dict = serializer.to_dict(obj)
        obj_dict_str = orjson.dumps(
            obj_dict,
            option=orjson.OPT_INDENT_2 | orjson.OPT_OMIT_MICROSECONDS,
            default=orjson_default,
        ).decode()

        snake_case_type_name = CaseUtil.pascal_to_snake_case(sample_type.__name__)
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(obj_dict_str)

    RegressionGuard().verify_all()


def test_to_dict_serialize_primitive():
    """Test OneWaySerializer.to_dict method with serialize_primitive flag."""

    serializer = OneWaySerializer(serialize_primitive=True)

    for sample_type in _SAMPLE_TYPES:
        obj = sample_type().build()
        obj_dict = serializer.to_dict(obj)
        obj_dict_str = orjson.dumps(obj_dict, option=orjson.OPT_INDENT_2).decode()

        snake_case_type_name = CaseUtil.pascal_to_snake_case(sample_type.__name__)
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(obj_dict_str)

    RegressionGuard().verify_all()


def test_to_dict_pascalize_keys():
    """Test OneWaySerializer.to_dict method with pascalize_keys flag."""

    serializer = OneWaySerializer(serialize_primitive=True, pascalize_keys=True)

    for sample_type in _SAMPLE_TYPES:
        obj = sample_type().build()
        obj_dict = serializer.to_dict(obj)
        obj_dict_str = orjson.dumps(obj_dict, option=orjson.OPT_INDENT_2).decode()

        snake_case_type_name = CaseUtil.pascal_to_snake_case(sample_type.__name__)
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(obj_dict_str)

    RegressionGuard().verify_all()

if __name__ == "__main__":
    pytest.main([__file__])
