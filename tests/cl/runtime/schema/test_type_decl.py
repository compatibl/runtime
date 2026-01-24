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
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.ui.ui_app_state import UiAppState
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_composite import StubDataclassComposite
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_double_derived import StubDataclassDoubleDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_dict_fields import StubDataclassListDictFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import StubDataclassListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields import StubDataclassNestedFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_optional_fields import StubDataclassOptionalFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_other_derived import StubDataclassOtherDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields import StubDataclassPrimitiveFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_singleton import StubDataclassSingleton
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_handlers import StubHandlers
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_aliased import StubDataclassAliased
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_tuple_fields import StubDataclassTupleFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_versioned import StubDataclassVersioned

_SAMPLE_TYPES = [
    UiAppState,
    StubDataclass,
    StubDataclassNestedFields,
    StubDataclassComposite,
    StubDataclassDerived,
    StubDataclassDoubleDerived,
    StubDataclassOtherDerived,
    StubDataclassListFields,
    StubDataclassTupleFields,
    StubDataclassOptionalFields,
    # TODO: StubDataclassDictFields,
    # TODO: StubDataclassDictListFields,
    StubDataclassListDictFields,
    StubDataclassPrimitiveFields,
    StubDataclassSingleton,
    StubDataclassAliased,
    StubHandlers,
    StubDataclass,
    StubDataclassVersioned,
]


def test_type_decl():
    """Test type decls generated for stub records."""
    for record_type in _SAMPLE_TYPES:

        # Get type declaration
        type_name = typename(record_type)
        type_decl: TypeDecl = TypeDecl.for_type(record_type)
        assert type_decl is not None

        # Create YAML string for the declaration
        type_decl_str = BootstrapSerializers.YAML.serialize(type_decl)

        # Record in regression guard
        guard = RegressionGuard(prefix=type_name)
        guard.write(type_decl_str)
    RegressionGuard().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
