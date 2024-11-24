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
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.schema.handler_declare_block_decl import HandlerDeclareBlockDecl
from cl.runtime.schema.type_decl import TypeDecl
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived_record import StubDataclassDerivedRecord

type_decl_dict = {
    "Module": {"ModuleName": "Cl.Runtime.Backend.Core"},
    "Name": "UiAppState",
    "DisplayKind": "Basic",
    "Elements": [
        {"Value": {"Type": "String"}, "Name": "User", "Optional": True},
    ],
    "Keys": ["User"],
}


class TestClass:

    def not_a_handler_method(self):
        pass

    def run_is_a_handler_method(self):
        pass


def to_snake_case(data):
    if isinstance(data, dict):
        return {
            CaseUtil.pascal_to_snake_case(key) if isinstance(key, str) else key: to_snake_case(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [to_snake_case(item) for item in data]
    else:
        return data


def test_to_type_decl_dict():
    """Test TypeDecl.to_type_decl_dict method."""

    record_types = [UiAppState, StubDataclassRecord]
    for record_type in record_types:
        type_decl = TypeDecl.for_type(record_type)
        type_decl_dict_ = type_decl.to_type_decl_dict()

        assert isinstance(type_decl_dict_, dict), f"Expected type: Dict, but got {type(type_decl_dict_)}"
        assert len(type_decl_dict_) > 0, f"Result dictionary is empty!"


def test_type_without_handlers():
    type_decl = TypeDecl.for_type(StubDataclassDerivedRecord)

    assert type_decl.name == "StubDataclassDerivedRecord"
    assert type_decl.comment == "Stub derived class."
    assert type_decl.declare is None, f"Class: {StubDataclassDerivedRecord} should not have handlers!"


def test_type_with_handlers():
    type_decl: TypeDecl = TypeDecl.for_type(TestClass)

    assert type_decl is not None

    handler_decl: HandlerDeclareBlockDecl = type_decl.declare
    assert handler_decl is not None

    handlers = handler_decl.handlers
    assert len(handlers) == 1, f"One handler expected!"


if __name__ == "__main__":
    pytest.main([__file__])
