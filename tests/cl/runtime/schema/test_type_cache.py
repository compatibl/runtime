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
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.schema.type_info_cache import TypeInfoCache
from cl.runtime.schema.type_kind import TypeKind
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubIntEnum
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_underscore import _StubDataclassUnderscore  # noqa
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_double_underscore import __StubDataclassDoubleUnderscore  # noqa

def test_rebuild_cache():
    """Test TypeInfoCache.reload_cache method, this also generates and saves a new TypeInfo.csv file."""
    TypeInfoCache.rebuild()


def test_get_qual_name():
    """Test getting class path from class."""

    # Base class
    base_path = f"{StubDataclass.__module__}.{StubDataclass.__name__}"
    assert TypeInfoCache.get_qual_name_from_class(StubDataclass) == base_path

    # Derived class
    derived_path = f"{StubDataclassDerived.__module__}.{StubDataclassDerived.__name__}"
    assert TypeInfoCache.get_qual_name_from_class(StubDataclassDerived) == derived_path


def test_from_type_name():
    """Test getting class from type names."""

    assert TypeInfoCache.get_class_from_type_name("TypeDecl") is TypeDecl
    assert TypeInfoCache.get_class_from_type_name("StubDataclass") is StubDataclass


def test_from_qual_name():
    """Test getting class from qual names."""

    # Classes that is already imported
    for imported_class in [TypeInfoCache, TypeDecl, StubDataclass]:
        class_info_path = f"{imported_class.__module__}.{imported_class.__name__}"
        assert TypeInfoCache.get_class_from_qual_name(class_info_path) == imported_class

    # Class that is dynamically imported on demand
    do_no_import_class_path = (
        "stubs.cl.runtime.records.for_dataclasses.stub_dataclass_do_not_import.StubDataclassDoNotImport"
    )
    do_no_import_class = TypeInfoCache.get_class_from_qual_name(do_no_import_class_path)
    assert do_no_import_class_path == f"{do_no_import_class.__module__}.{do_no_import_class.__name__}"

    # Module does not exist error
    with pytest.raises(RuntimeError):
        path_with_unknown_module = "unknown_module.StubDataclassDoNotImport"
        TypeInfoCache.get_class_from_qual_name(path_with_unknown_module)

    # Class does not exist error
    with pytest.raises(RuntimeError):
        path_with_unknown_class = "stubs.cl.runtime.records.for_dataclasses.stub_dataclass_do_not_import.UnknownClass"
        TypeInfoCache.get_class_from_qual_name(path_with_unknown_class)


def test_get_classes():
    """Test TypeInfoCache.get_classes method."""

    data_types = TypeInfoCache.get_classes(
        type_kinds=(
            TypeKind.DATA,
            TypeKind.KEY,
            TypeKind.RECORD,
        )
    )

    # Included data types
    assert TypeDecl in data_types
    assert StubDataclass in data_types

    # Excluded data types
    assert RecordMixin not in data_types
    assert _StubDataclassUnderscore not in data_types
    assert __StubDataclassDoubleUnderscore not in data_types

    enum_types = TypeInfoCache.get_classes(type_kinds=(TypeKind.ENUM,))

    # Included enum types
    assert StubIntEnum in enum_types

    # Excluded enum types
    assert Enum not in enum_types
    assert IntEnum not in enum_types


if __name__ == "__main__":
    pytest.main([__file__])
