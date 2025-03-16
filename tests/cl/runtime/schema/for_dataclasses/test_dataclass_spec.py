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
from cl.runtime.backend.core.ui_app_state import UiAppState
from cl.runtime.schema.dataclass_spec import DataclassSpec
from cl.runtime.serializers.yaml_serializer import YamlSerializer
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
from stubs.cl.runtime import StubHandlers
from stubs.cl.runtime import StubIntEnum
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_aliased_record import StubDataclassAliasedRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_tuple_fields import StubDataclassTupleFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_versioned_record import StubDataclassVersionedRecord
from stubs.cl.runtime.views.stub_viewers import StubViewers

_FROM_CLASS_VALID_CASES = [
    StubDataclassRecord,
    StubDataclassNestedFields,
    StubDataclassComposite,
    StubDataclassDerivedRecord,
    StubDataclassDerivedFromDerivedRecord,
    StubDataclassOtherDerivedRecord,
    StubDataclassListFields,
    StubDataclassTupleFields,
    StubDataclassOptionalFields,
    StubDataclassDictFields,
    StubDataclassDictListFields,
    StubDataclassListDictFields,
    StubDataclassPrimitiveFields,
    StubDataclassSingleton,
    StubDataclassAliasedRecord,
    StubHandlers,
    StubViewers,
    StubDataclassVersionedRecord,
    UiAppState,
]

_FROM_CLASS_EXCEPTION_CASES = [
    type,
    StubIntEnum,
]

yaml_serializer = YamlSerializer(omit_type=True).build()


def test_from_class():
    """Test EnumSpec.from_class method."""
    for test_case in _FROM_CLASS_VALID_CASES:

        # Get enum spec and serialize as YAML
        type_spec = DataclassSpec.from_class(test_case)
        type_spec_str = yaml_serializer.serialize(type_spec)

        # Record in RegressionGuard
        guard = RegressionGuard(channel=type_spec.type_name)
        guard.write(type_spec_str)
    RegressionGuard().verify_all()


def test_from_class_exceptions():
    """Test EnumSpec.from_class method exceptions."""
    for test_case in _FROM_CLASS_EXCEPTION_CASES:
        with pytest.raises(Exception):
            DataclassSpec.from_class(test_case)


if __name__ == "__main__":
    pytest.main([__file__])
