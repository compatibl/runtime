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
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.serializers.json_serializers import JsonSerializers
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
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_tuple_fields import StubDataclassTupleFields

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
    StubDataclassTupleFields,
]


def test_default():
    """Test DataSerializer.to_json method."""

    for sample_type in _SAMPLE_TYPES:

        # Serialize to JSON
        obj = sample_type().build()
        result_str = JsonSerializers.DEFAULT.serialize(obj)

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(sample_type.__name__)
        guard = RegressionGuard(prefix=snake_case_type_name).build()
        guard.write(result_str)

    RegressionGuard().build().verify_all()


def test_compact():
    """Test DataSerializer.to_json method."""

    for sample_type in _SAMPLE_TYPES:

        # Serialize to JSON
        obj = sample_type().build()
        result_str = JsonSerializers.COMPACT.serialize(obj)

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(sample_type.__name__)
        guard = RegressionGuard(prefix=snake_case_type_name).build()
        guard.write(result_str)

    RegressionGuard().build().verify_all()


def test_for_reporting():
    """Test DataSerializer.to_json method."""

    for sample_type in _SAMPLE_TYPES:

        # Serialize to JSON
        obj = sample_type().build()
        result_str = JsonSerializers.FOR_REPORTING.serialize(obj)

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(sample_type.__name__)
        guard = RegressionGuard(prefix=snake_case_type_name).build()
        guard.write(result_str)

    RegressionGuard().build().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
