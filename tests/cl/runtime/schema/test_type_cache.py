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
from cl.runtime import RecordMixin
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.schema.type_kind import TypeKind
from stubs.cl.runtime import StubDataclass, StubDataclassKey, StubDataclassData
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubIntEnum
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_double_underscore import (  # noqa
    __StubDataclassDoubleUnderscore,
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_underscore import _StubDataclassUnderscore  # noqa


def test_rebuild_cache():
    """Test TypeCache.reload_cache method, this also generates and saves a new TypeInfo.csv file."""
    TypeCache.rebuild()


def test_get_qual_name():
    """Test getting class path from class."""

    # Base class
    base_path = f"{StubDataclass.__module__}.{StubDataclass.__name__}"
    assert TypeCache.get_qual_name_from_class(StubDataclass) == base_path

    # Derived class
    derived_path = f"{StubDataclassDerived.__module__}.{StubDataclassDerived.__name__}"
    assert TypeCache.get_qual_name_from_class(StubDataclassDerived) == derived_path


def test_from_type_name():
    """Test getting class from type names."""

    assert TypeCache.get_class_from_type_name("TypeDecl") is TypeDecl
    assert TypeCache.get_class_from_type_name("StubDataclass") is StubDataclass


def test_from_qual_name():
    """Test getting class from qual names."""

    # Classes that is already imported
    for imported_class in [TypeCache, TypeDecl, StubDataclass]:
        class_info_path = f"{imported_class.__module__}.{imported_class.__name__}"
        assert TypeCache.get_class_from_qual_name(class_info_path) == imported_class

    # Class that is dynamically imported on demand
    do_no_import_class_path = (
        "stubs.cl.runtime.records.for_dataclasses.stub_dataclass_do_not_import.StubDataclassDoNotImport"
    )
    do_no_import_class = TypeCache.get_class_from_qual_name(do_no_import_class_path)
    assert do_no_import_class_path == f"{do_no_import_class.__module__}.{do_no_import_class.__name__}"

    # Module does not exist error
    with pytest.raises(RuntimeError):
        path_with_unknown_module = "unknown_module.StubDataclassDoNotImport"
        TypeCache.get_class_from_qual_name(path_with_unknown_module)

    # Class does not exist error
    with pytest.raises(RuntimeError):
        path_with_unknown_class = "stubs.cl.runtime.records.for_dataclasses.stub_dataclass_do_not_import.UnknownClass"
        TypeCache.get_class_from_qual_name(path_with_unknown_class)


def test_get_classes():
    """Test TypeCache.get_classes method."""

    # Included in data types
    data_types = TypeCache.get_classes(type_kind=TypeKind.DATA)
    assert StubDataclassData in data_types
    # Excluded from data types
    assert DataMixin not in data_types
    assert RecordMixin not in data_types
    assert _StubDataclassUnderscore not in data_types
    assert __StubDataclassDoubleUnderscore not in data_types

    # Included in record types
    record_types = TypeCache.get_classes(type_kind=TypeKind.RECORD)
    assert StubDataclass in record_types
    assert TypeDecl in record_types
    # Excluded from record types
    assert RecordMixin not in record_types
    assert StubDataclassKey not in record_types
    assert StubDataclassData not in record_types

    # Included in key types
    key_types = TypeCache.get_classes(type_kind=TypeKind.KEY)
    assert StubDataclassKey in key_types
    # Excluded from key types
    assert KeyMixin not in record_types
    assert StubDataclassData not in key_types

    # Included in enum types
    enum_types = TypeCache.get_classes(type_kind=TypeKind.ENUM)
    assert StubIntEnum in enum_types
    # Excluded from enum types
    assert Enum not in enum_types
    assert IntEnum not in enum_types


if __name__ == "__main__":
    pytest.main([__file__])
