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
from cl.runtime import ClassInfo
from stubs.cl.runtime import StubAttrsCyclicA
from stubs.cl.runtime import StubAttrsCyclicB
from stubs.cl.runtime import StubAttrsData
from stubs.cl.runtime import StubAttrsDerivedData
from stubs.cl.runtime import StubAttrsDerivedFromDerivedData
from stubs.cl.runtime import StubAttrsDerivedFromDerivedRecord
from stubs.cl.runtime import StubAttrsDerivedRecord
from stubs.cl.runtime import StubAttrsDictFields
from stubs.cl.runtime import StubAttrsDictListFields
from stubs.cl.runtime import StubAttrsDoNotImport
from stubs.cl.runtime import StubAttrsListDictFields
from stubs.cl.runtime import StubAttrsListFields
from stubs.cl.runtime import StubAttrsNestedFields
from stubs.cl.runtime import StubAttrsNestedFieldsKey
from stubs.cl.runtime import StubAttrsOtherDerivedRecord
from stubs.cl.runtime import StubAttrsPrimitiveFields
from stubs.cl.runtime import StubAttrsPrimitiveFieldsKey
from stubs.cl.runtime import StubAttrsRecord
from stubs.cl.runtime import StubAttrsRecordKey
from stubs.cl.runtime import StubAttrsSingleton
from stubs.cl.runtime import StubAttrsSingletonKey


def test_get_class_path():
    """Test getting class path from class."""

    # Base class
    base_path = f"{StubAttrsRecord.__module__}.{StubAttrsRecord.__name__}"
    assert ClassInfo.get_class_path(StubAttrsRecord) == base_path

    # Derived class
    derived_path = f"{StubAttrsDerivedRecord.__module__}.{StubAttrsDerivedRecord.__name__}"
    assert ClassInfo.get_class_path(StubAttrsDerivedRecord) == derived_path


def test_split_class_path():
    """Test splitting class path into module and class name."""

    # Base class
    base_path = f"{StubAttrsRecord.__module__}.{StubAttrsRecord.__name__}"
    base_result = StubAttrsRecord.__module__, StubAttrsRecord.__name__
    assert ClassInfo.split_class_path(base_path) == base_result

    # Derived class
    derived_path = f"{StubAttrsDerivedRecord.__module__}.{StubAttrsDerivedRecord.__name__}"
    derived_result = StubAttrsDerivedRecord.__module__, StubAttrsDerivedRecord.__name__
    assert ClassInfo.split_class_path(derived_path) == derived_result


def test_get_class_type():
    """Test getting class from module and class strings."""

    # Class that is already imported
    assert ClassInfo.get_class_type(ClassInfo.__module__, ClassInfo.__name__) == ClassInfo

    # Class that is dynamically imported on demand
    do_no_import_module_name = "stubs.cl.runtime.classes.attrs.stub_attrs_do_not_import"
    do_no_import_class_name = "StubAttrsDoNotImport"
    do_no_import_class = ClassInfo.get_class_type(do_no_import_module_name, do_no_import_class_name)
    assert do_no_import_class.__module__ == do_no_import_module_name
    assert do_no_import_class.__name__ == do_no_import_class_name

    # Module does not exist error
    unknown_name = "aBcDeF"
    with pytest.raises(RuntimeError):
        ClassInfo.get_class_type(unknown_name, do_no_import_class_name)

    # Class does not exist error
    with pytest.raises(RuntimeError):
        ClassInfo.get_class_type(do_no_import_module_name, unknown_name)

    # Dot-delimited class name error
    with pytest.raises(RuntimeError):
        ClassInfo.get_class_type(do_no_import_module_name, "a.b")

    # Call one more time and confirm that method results are cached
    assert ClassInfo.get_class_type(ClassInfo.__module__, ClassInfo.__name__) == ClassInfo
    assert ClassInfo.get_class_type.cache_info().hits > 0


def test_get_inheritance_chain():
    """Test getting class path from class."""

    key_class = "StubAttrsRecordKey"
    base_class = "StubAttrsRecord"
    derived_class = "StubAttrsDerivedRecord"

    # Key class, returns self
    assert ClassInfo.get_inheritance_chain(StubAttrsRecordKey) == [key_class]

    # Common base class, returns self and key class
    assert ClassInfo.get_inheritance_chain(StubAttrsRecord) == [base_class, key_class]

    # Derived class, returns self, common base and key
    assert ClassInfo.get_inheritance_chain(StubAttrsDerivedRecord) == [derived_class, base_class, key_class]

    # Invoke for a type that does not have a key class
    with pytest.raises(RuntimeError):
        ClassInfo.get_inheritance_chain(StubAttrsData)

    # Call one more time and confirm that method results are cached
    assert ClassInfo.get_inheritance_chain(StubAttrsRecord) == [base_class, key_class]
    assert ClassInfo.get_inheritance_chain.cache_info().hits > 0


def test_get_table():
    """Test getting table name from class."""

    # Key class
    assert ClassInfo.get_table(StubAttrsRecordKey) == "StubAttrsRecord"

    # Common base class
    assert ClassInfo.get_table(StubAttrsRecord) == "StubAttrsRecord"

    # Derived class
    assert ClassInfo.get_table(StubAttrsDerivedRecord) == "StubAttrsRecord"

    # Error if a type does not have key class
    with pytest.raises(RuntimeError):
        ClassInfo.get_table(StubAttrsData)

    # Call one more time and confirm that method results are cached
    assert ClassInfo.get_table(StubAttrsRecordKey) == "StubAttrsRecord"
    assert ClassInfo.get_table.cache_info().hits > 0


def test_to_from_dict():
    """Test dictionary serialization roundtrip."""

    # List of types for which serialization will be tested
    # TODO: Support remaining classes
    stub_types = [
        # StubAttrsCyclicA,
        # StubAttrsCyclicB,
        StubAttrsData,
        StubAttrsDerivedData,
        StubAttrsDerivedFromDerivedData,
        StubAttrsDerivedFromDerivedRecord,
        StubAttrsDerivedRecord,
        # StubAttrsDictFields,
        # StubAttrsDictListFields,
        # StubAttrsDoNotImport,
        # StubAttrsListDictFields,
        StubAttrsListFields,
        # StubAttrsNestedFields,
        StubAttrsNestedFieldsKey,
        StubAttrsOtherDerivedRecord,
        StubAttrsPrimitiveFields,
        StubAttrsPrimitiveFieldsKey,
        StubAttrsRecord,
        StubAttrsRecordKey,
        StubAttrsSingleton,
        StubAttrsSingletonKey,
    ]

    for stub_type in stub_types:
        # Create a stub type instance with default field values
        obj = stub_type()

        # Serialize to dict
        data = ClassInfo.to_dict(obj)

        # Restore from dict
        restored_obj = ClassInfo.from_dict(stub_type, data)

        # Compare
        assert obj == restored_obj


if __name__ == "__main__":
    pytest.main([__file__])