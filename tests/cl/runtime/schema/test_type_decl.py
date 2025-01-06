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
from dataclasses import asdict
from cl.runtime.backend.core.ui_app_state import UiAppState
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.handler_declare_block_decl import HandlerDeclareBlockDecl
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.serialization.dict_serializer import DictSerializer
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
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_aliased_record import StubDataclassAliasedRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_final_key import StubDataclassFinalKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_final_record import StubDataclassFinalRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_final_record import StubDataclassNestedFinalRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_tuple_fields import StubDataclassTupleFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_versioned_record import StubDataclassVersionedRecord

_SAMPLE_TYPES = [
    UiAppState,
    StubDataclassRecord,
    StubDataclassNestedFields,
    StubDataclassComposite,
    StubDataclassDerivedRecord,
    StubDataclassDerivedFromDerivedRecord,
    StubDataclassOtherDerivedRecord,
    StubDataclassListFields,
    StubDataclassTupleFields,
    StubDataclassOptionalFields,
    # TODO: StubDataclassDictFields,
    # TODO: StubDataclassDictListFields,
    StubDataclassListDictFields,
    StubDataclassPrimitiveFields,
    StubDataclassSingleton,
    StubDataclassAliasedRecord,
    StubHandlers,
    StubDataclassRecord,
    StubDataclassVersionedRecord,
    StubDataclassFinalKey,
    StubDataclassFinalRecord,
    StubDataclassNestedFinalRecord,
]


def test_type_decl():
    """Test type decls generated for stub records."""
    for record_type in _SAMPLE_TYPES:

        # Get type declaration
        type_name = TypeUtil.name(record_type)
        type_decl: TypeDecl = TypeDecl.for_type(record_type)
        assert type_decl is not None

        # Use native dataclasses.asdict to ensure we do not rely on the functionality being tested for serialization
        type_decl_dict = asdict(type_decl)  # noqa
        guard = RegressionGuard(channel=type_name)
        guard.write(type_decl_dict)
    RegressionGuard().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
