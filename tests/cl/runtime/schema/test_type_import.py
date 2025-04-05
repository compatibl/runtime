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
from cl.runtime import TypeImport
from stubs.cl.runtime import StubDataclassData
from stubs.cl.runtime import StubDataclassDerivedRecord
from stubs.cl.runtime import StubDataclassRecord


def test_get_class_path():
    """Test getting class path from class."""

    # Base class
    base_path = f"{StubDataclassRecord.__module__}.{StubDataclassRecord.__name__}"
    assert TypeImport.get_class_path(StubDataclassRecord) == base_path

    # Derived class
    derived_path = f"{StubDataclassDerivedRecord.__module__}.{StubDataclassDerivedRecord.__name__}"
    assert TypeImport.get_class_path(StubDataclassDerivedRecord) == derived_path


def test_split_class_path():
    """Test splitting class path into module and class name."""

    # Base class
    base_path = f"{StubDataclassRecord.__module__}.{StubDataclassRecord.__name__}"
    base_result = StubDataclassRecord.__module__, StubDataclassRecord.__name__
    assert TypeImport.split_class_path(base_path) == base_result

    # Derived class
    derived_path = f"{StubDataclassDerivedRecord.__module__}.{StubDataclassDerivedRecord.__name__}"
    derived_result = StubDataclassDerivedRecord.__module__, StubDataclassDerivedRecord.__name__
    assert TypeImport.split_class_path(derived_path) == derived_result


def test_get_class_type():
    """Test getting class from module and class strings."""

    # Class that is already imported
    class_info_path = f"{TypeImport.__module__}.{TypeImport.__name__}"
    assert TypeImport.get_class_type(class_info_path) == TypeImport

    # Class that is dynamically imported on demand
    do_no_import_class_path = (
        "stubs.cl.runtime.records.for_dataclasses.stub_dataclass_do_not_import.StubDataclassDoNotImport"
    )
    do_no_import_class = TypeImport.get_class_type(do_no_import_class_path)
    assert do_no_import_class_path == f"{do_no_import_class.__module__}.{do_no_import_class.__name__}"

    # Module does not exist error
    unknown_name = "aBcDeF"
    with pytest.raises(RuntimeError):
        path_with_unknown_module = "unknown_module.StubDataclassDoNotImport"
        TypeImport.get_class_type(path_with_unknown_module)

    # Class does not exist error
    with pytest.raises(RuntimeError):
        path_with_unknown_class = "stubs.cl.runtime.records.for_dataclasses.stub_dataclass_do_not_import.UnknownClass"
        TypeImport.get_class_type(path_with_unknown_class)

    # Call one more time and confirm that method results are cached
    assert TypeImport.get_class_type(class_info_path) == TypeImport
    assert TypeImport.get_class_type.cache_info().hits > 0


def test_get_inheritance_chain():
    """Test getting class path from class."""

    base_class = "StubDataclassRecord"
    derived_class = "StubDataclassDerivedRecord"

    # Common base class, returns self and key class
    assert TypeImport.get_inheritance_chain(StubDataclassRecord) == [base_class]

    # Derived class, returns self, common base and key
    assert TypeImport.get_inheritance_chain(StubDataclassDerivedRecord) == [derived_class, base_class]

    # Invoke for a type that does not have a key class
    with pytest.raises(RuntimeError):
        TypeImport.get_inheritance_chain(StubDataclassData)

    # Call one more time and confirm that method results are cached
    assert TypeImport.get_inheritance_chain(StubDataclassRecord) == [base_class]
    assert TypeImport.get_inheritance_chain.cache_info().hits > 0


if __name__ == "__main__":
    pytest.main([__file__])
