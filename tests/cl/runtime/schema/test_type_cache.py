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
from enum import Enum
from enum import IntEnum
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.schema.type_kind import TypeKind
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassData
from stubs.cl.runtime import StubDataclassKey
from stubs.cl.runtime import StubIntEnum
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_double_underscore import (  # noqa
    __StubDataclassDoubleUnderscore,
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_underscore import _StubDataclassUnderscore  # noqa


def test_rebuild_cache():
    """Test TypeCache.reload_cache method, this also generates and saves a new TypeInfo.csv file."""
    TypeCache.rebuild()


def test_is_known_type():
    """Test is_known_type method."""

    # Valid cases
    assert TypeCache.is_known_type(StubDataclass)
    assert TypeCache.is_known_type(StubDataclassKey)
    assert TypeCache.is_known_type(StubDataclassData)

    # Invalid cases
    assert not TypeCache.is_known_type(123)  # noqa


def test_guard_known_type():
    """Test guard_known_type method."""

    # Valid cases
    assert TypeCache.guard_known_type(StubDataclass)
    assert TypeCache.guard_known_type(StubDataclass, type_kind=TypeKind.RECORD)
    assert TypeCache.guard_known_type(StubDataclassKey)
    assert TypeCache.guard_known_type(StubDataclassKey, type_kind=TypeKind.KEY)
    assert TypeCache.guard_known_type(StubDataclassData)
    assert TypeCache.guard_known_type(StubDataclassData, type_kind=TypeKind.DATA)

    # Invalid cases
    assert not TypeCache.guard_known_type(123, raise_on_fail=False)
    with pytest.raises(Exception):
        TypeCache.guard_known_type(123)

    # Not a record
    assert not TypeCache.guard_known_type(StubDataclassData, type_kind=TypeKind.RECORD, raise_on_fail=False)
    with pytest.raises(Exception):
        TypeCache.guard_known_type(StubDataclassData, type_kind=TypeKind.RECORD)


def test_get_type_info():
    """Test get_type_name method."""

    # Valid cases
    assert TypeCache.get_type_info(StubDataclass).type_kind == TypeKind.RECORD
    assert TypeCache.get_type_info("StubDataclass").type_kind == TypeKind.RECORD
    assert TypeCache.get_type_info(StubDataclassKey).type_kind == TypeKind.KEY
    assert TypeCache.get_type_info("StubDataclassKey").type_kind == TypeKind.KEY
    assert TypeCache.get_type_info(StubDataclassData).type_kind == TypeKind.DATA
    assert TypeCache.get_type_info("StubDataclassData").type_kind == TypeKind.DATA

    # Invalid cases
    with pytest.raises(Exception):
        # Not a known type
        TypeCache.get_type_info(123)  # noqa
    with pytest.raises(Exception):
        # Not a known type name
        TypeCache.get_type_info("123")  # noqa


def test_get_type_name():
    """Test get_type_name method."""

    # Valid cases
    assert TypeCache.get_type_name(StubDataclass) == "StubDataclass"
    assert TypeCache.get_type_name(StubDataclassKey) == "StubDataclassKey"
    assert TypeCache.get_type_name(StubDataclassData) == "StubDataclassData"

    # Invalid cases
    with pytest.raises(Exception):
        # Not a known type
        TypeCache.get_type_name(123)  # noqa


def test_get_qual_name():
    """Test get_qual_name method."""

    # Valid cases
    assert TypeCache.get_qual_name(StubDataclass) == f"{StubDataclass.__module__}.{StubDataclass.__name__}"
    assert TypeCache.get_qual_name(StubDataclassKey) == f"{StubDataclassKey.__module__}.{StubDataclassKey.__name__}"
    assert TypeCache.get_qual_name(StubDataclassData) == f"{StubDataclassData.__module__}.{StubDataclassData.__name__}"

    # Invalid cases
    with pytest.raises(Exception):
        # Not a known type
        TypeCache.get_qual_name(123)  # noqa


def test_from_type_name():
    """Test getting class from type names."""

    assert TypeCache.from_type_name("TypeDecl") is TypeDecl
    assert TypeCache.from_type_name("StubDataclass") is StubDataclass
    assert TypeCache.from_type_name("StubDataclassKey") is StubDataclassKey
    assert TypeCache.from_type_name("StubDataclassData") is StubDataclassData


def test_from_qual_name():
    """Test getting class from qual names."""

    # Classes that is already imported
    for imported_class in [TypeCache, TypeDecl, StubDataclass]:
        class_info_path = f"{imported_class.__module__}.{imported_class.__name__}"
        assert TypeCache.from_qual_name(class_info_path) == imported_class

    # Class that is dynamically imported on demand
    do_no_import_class_path = (
        "stubs.cl.runtime.records.for_dataclasses.stub_dataclass_do_not_import.StubDataclassDoNotImport"
    )
    do_no_import_class = TypeCache.from_qual_name(do_no_import_class_path)
    assert do_no_import_class_path == f"{do_no_import_class.__module__}.{do_no_import_class.__name__}"

    # Module does not exist error
    with pytest.raises(RuntimeError):
        path_with_unknown_module = "unknown_module.StubDataclassDoNotImport"
        TypeCache.from_qual_name(path_with_unknown_module)

    # Class does not exist error
    with pytest.raises(RuntimeError):
        path_with_unknown_class = "stubs.cl.runtime.records.for_dataclasses.stub_dataclass_do_not_import.UnknownClass"
        TypeCache.from_qual_name(path_with_unknown_class)


def test_get_classes():
    """Test TypeCache.get_classes method."""

    # Included in data types
    data_types = TypeCache.get_types(type_kind=TypeKind.DATA)
    assert DataMixin in data_types
    assert StubDataclassData in data_types
    # Excluded from data types
    assert KeyMixin not in data_types
    assert RecordMixin not in data_types
    assert _StubDataclassUnderscore not in data_types
    assert __StubDataclassDoubleUnderscore not in data_types

    # Included in record types
    record_types = TypeCache.get_types(type_kind=TypeKind.RECORD)
    assert RecordMixin in record_types
    assert StubDataclass in record_types
    assert TypeDecl in record_types
    # Excluded from record types
    assert DataMixin not in record_types
    assert KeyMixin not in record_types
    assert StubDataclassKey not in record_types
    assert StubDataclassData not in record_types

    # Included in key types
    key_types = TypeCache.get_types(type_kind=TypeKind.KEY)
    assert KeyMixin in key_types
    assert StubDataclassKey in key_types
    # Excluded from key types
    assert DataMixin not in key_types
    assert RecordMixin not in key_types
    assert StubDataclassData not in key_types

    # Included in enum types
    enum_types = TypeCache.get_types(type_kind=TypeKind.ENUM)
    assert StubIntEnum in enum_types
    # Excluded from enum types
    assert Enum not in enum_types  # TODO: Enum base is excluded, review
    assert IntEnum not in enum_types  # TODO: IntEnum base is excluded, review
    assert DataMixin not in enum_types
    assert KeyMixin not in enum_types
    assert RecordMixin not in enum_types


if __name__ == "__main__":
    pytest.main([__file__])
