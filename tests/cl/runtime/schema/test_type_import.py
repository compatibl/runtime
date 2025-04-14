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
from cl.runtime import RecordMixin
from cl.runtime import TypeImport
from cl.runtime.records.protocols import is_key_or_record
from cl.runtime.schema.type_decl import TypeDecl
from stubs.cl.runtime import StubDataclassDerivedRecord
from stubs.cl.runtime import StubDataclassRecord


def test_rebuild_cache():
    """Test TypeImport.reload_cache method, this also generates and saves a new imports.txt file."""
    TypeImport.rebuild_cache()


def test_get_qual_name():
    """Test getting class path from class."""

    # Base class
    base_path = f"{StubDataclassRecord.__module__}.{StubDataclassRecord.__name__}"
    assert TypeImport.get_qual_name_from_class(StubDataclassRecord) == base_path

    # Derived class
    derived_path = f"{StubDataclassDerivedRecord.__module__}.{StubDataclassDerivedRecord.__name__}"
    assert TypeImport.get_qual_name_from_class(StubDataclassDerivedRecord) == derived_path


def test_from_type_name():
    """Test TypeImport.class_from_type_name() method."""

    assert TypeImport.get_class_from_type_name("TypeDecl") is TypeDecl
    assert TypeImport.get_class_from_type_name("StubDataclassRecord") is StubDataclassRecord


def test_from_qual_name():
    """Test getting class from module and class strings."""

    # Classes that is already imported
    for imported_class in [TypeImport, TypeDecl, StubDataclassRecord]:
        class_info_path = f"{imported_class.__module__}.{imported_class.__name__}"
        assert TypeImport.get_class_from_qual_name(class_info_path) == imported_class

    # Class that is dynamically imported on demand
    do_no_import_class_path = (
        "stubs.cl.runtime.records.for_dataclasses.stub_dataclass_do_not_import.StubDataclassDoNotImport"
    )
    do_no_import_class = TypeImport.get_class_from_qual_name(do_no_import_class_path)
    assert do_no_import_class_path == f"{do_no_import_class.__module__}.{do_no_import_class.__name__}"

    # Module does not exist error
    with pytest.raises(RuntimeError):
        path_with_unknown_module = "unknown_module.StubDataclassDoNotImport"
        TypeImport.get_class_from_qual_name(path_with_unknown_module)

    # Class does not exist error
    with pytest.raises(RuntimeError):
        path_with_unknown_class = "stubs.cl.runtime.records.for_dataclasses.stub_dataclass_do_not_import.UnknownClass"
        TypeImport.get_class_from_qual_name(path_with_unknown_class)


def test_cached_classes():
    """Test TypeImport.cached_type_names method."""

    records = TypeImport.get_cached_classes(predicate=is_key_or_record)

    # Included
    assert TypeDecl in records
    assert StubDataclassRecord in records

    # Excluded
    assert RecordMixin not in records


if __name__ == "__main__":
    pytest.main([__file__])
