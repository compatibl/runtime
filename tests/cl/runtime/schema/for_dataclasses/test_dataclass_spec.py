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
from cl.runtime.schema.dataclass_spec import DataclassSpec
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.ui.ui_app_state import UiAppState
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
from stubs.cl.runtime import StubHandlers
from stubs.cl.runtime import StubIntEnum
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_aliased import StubDataclassAliased
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived_query import StubDataclassDerivedQuery
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields_query import StubDataclassNestedFieldsQuery
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields_query import (
    StubDataclassPrimitiveFieldsQuery,
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_query import StubDataclassQuery
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_tuple_fields import StubDataclassTupleFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_versioned import StubDataclassVersioned
from stubs.cl.runtime.views.stub_viewers import StubViewers

_FROM_CLASS_VALID_CASES = [
    StubDataclass,
    StubDataclassNestedFields,
    StubDataclassComposite,
    StubDataclassDerived,
    StubDataclassDoubleDerived,
    StubDataclassOtherDerived,
    StubDataclassListFields,
    StubDataclassTupleFields,
    StubDataclassOptionalFields,
    StubDataclassDictFields,
    StubDataclassDictListFields,
    StubDataclassListDictFields,
    StubDataclassPrimitiveFields,
    StubDataclassSingleton,
    StubDataclassAliased,
    StubHandlers,
    StubViewers,
    StubDataclassVersioned,
    StubDataclassQuery,
    StubDataclassDerivedQuery,
    StubDataclassPrimitiveFieldsQuery,
    StubDataclassNestedFieldsQuery,
    UiAppState,
]

_FROM_CLASS_EXCEPTION_CASES = [
    type,
    StubIntEnum,
]


def test_for_class():
    """Test EnumSpec.for_class method."""
    for test_case in _FROM_CLASS_VALID_CASES:

        # Get enum spec and serialize as YAML
        type_spec = DataclassSpec.for_class(test_case)
        type_spec_str = BootstrapSerializers.YAML.serialize(type_spec)

        # Record in RegressionGuard
        guard = RegressionGuard(channel=type_spec.type_name)
        guard.write(type_spec_str)
    RegressionGuard().verify_all()


def test_for_class_exceptions():
    """Test EnumSpec.for_class method exceptions."""
    for test_case in _FROM_CLASS_EXCEPTION_CASES:
        with pytest.raises(Exception):
            DataclassSpec.for_class(test_case)


if __name__ == "__main__":
    pytest.main([__file__])
