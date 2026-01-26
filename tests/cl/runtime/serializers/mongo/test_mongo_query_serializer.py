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
from cl.runtime.records.predicates import Exists
from cl.runtime.records.predicates import In
from cl.runtime.records.predicates import NotIn
from cl.runtime.records.predicates import Range
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.serializers.json_serializer import orjson_default
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived_query import StubDataclassDerivedQuery
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields_query import StubDataclassNestedFieldsQuery
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields_query import (
    StubDataclassPrimitiveFieldsQuery,
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_query import StubDataclassQuery

_SAMPLES = [
    StubDataclassQuery(
        id="abc",
    ).build(),
    StubDataclassDerivedQuery(
        derived_str_field=Exists(True),
    ).build(),
    StubDataclassDerivedQuery(
        derived_str_field=In(["def"]),
    ).build(),
    StubDataclassDerivedQuery(
        derived_str_field=NotIn(["def"]),
    ).build(),
    StubDataclassPrimitiveFieldsQuery(key_int_field=Range(gt=1, lt=10)).build(),
    StubDataclassNestedFieldsQuery().build(),
]


def test_unidirectional():
    """Test DataSerializer.serialize method with bidirectional=None."""

    # Create the serializer
    serializer = BootstrapSerializers.FOR_MONGO_QUERY

    for sample in _SAMPLES:

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
        guard = RegressionGuard(prefix=snake_case_type_name).build()
        guard.write(result_str)

    RegressionGuard.verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
