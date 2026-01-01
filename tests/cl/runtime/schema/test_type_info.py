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
from cl.runtime.records.typename import qualname
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.schema.type_kind import TypeKind
from cl.runtime.settings.env_settings import EnvSettings
from cl.runtime.settings.package_settings import PackageSettings
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassData
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassDoubleDerived
from stubs.cl.runtime import StubDataclassKey
from stubs.cl.runtime import StubDataclassOtherDerived
from stubs.cl.runtime import StubDataclassPrimitiveFields
from stubs.cl.runtime import StubIntEnum
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_double_underscore import (  # noqa
    __StubDataclassDoubleUnderscore,
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields_key import StubDataclassPrimitiveFieldsKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_underscore import _StubDataclassUnderscore  # noqa


def test_rebuild_cache():
    """Test TypeInfo.reload_cache method, this also generates and saves a new TypeInfo.csv file."""
    packages = PackageSettings.instance().get_packages()
    TypeInfo.rebuild(packages=packages)


def test_is_known_type():
    """Test is_known_type method."""

    # Valid cases
    assert TypeInfo.is_known_type(StubDataclass)
    assert TypeInfo.is_known_type(StubDataclassKey)
    assert TypeInfo.is_known_type(StubDataclassData)
    assert TypeInfo.is_known_type(TypeKind)

    # Invalid cases
    assert not TypeInfo.is_known_type(int)
    with pytest.raises(RuntimeError):
        # Not a type
        assert not TypeInfo.is_known_type(123)  # noqa


def test_is_known_type_name():
    """Test is_known_type_name method."""

    # Valid cases
    assert TypeInfo.is_known_type_name("StubDataclass")
    assert TypeInfo.is_known_type_name("StubDataclassKey")
    assert TypeInfo.is_known_type_name("StubDataclassData")
    assert TypeInfo.is_known_type_name("TypeKind")

    # Invalid cases
    assert not TypeInfo.is_known_type_name("123")
    assert not TypeInfo.is_known_type_name("int")
    with pytest.raises(RuntimeError):
        # Not a string
        assert not TypeInfo.is_known_type_name(StubDataclass)  # noqa


def test_guard_known_type():
    """Test guard_known_type method, will invoke and test guard_known_type_name as well."""

    # Valid cases
    assert TypeInfo.guard_known_type(StubDataclass)
    assert TypeInfo.guard_known_type(StubDataclass, type_kind=TypeKind.RECORD)
    assert TypeInfo.guard_known_type(StubDataclassKey)
    assert TypeInfo.guard_known_type(StubDataclassKey, type_kind=TypeKind.KEY)
    assert TypeInfo.guard_known_type(StubDataclassData)
    assert TypeInfo.guard_known_type(StubDataclassData, type_kind=TypeKind.DATA)

    # Invalid cases
    with pytest.raises(Exception, match="Function typename accepts only type"):
        # Raise an error even when raise_on_fail is False when the parameter is not a str or type
        TypeInfo.guard_known_type(123, raise_on_fail=False)
    with pytest.raises(Exception, match="Function typename accepts only type"):
        TypeInfo.guard_known_type(123)

    # Not a record
    assert not TypeInfo.guard_known_type(StubDataclassData, type_kind=TypeKind.RECORD, raise_on_fail=False)
    with pytest.raises(Exception):
        TypeInfo.guard_known_type(StubDataclassData, type_kind=TypeKind.RECORD)


def test_get_type_name_info():
    """Test get_type_name_info method."""

    # Valid cases
    assert TypeInfo.get_type_name_info("StubDataclass").type_kind == TypeKind.RECORD
    assert TypeInfo.get_type_name_info("StubDataclassKey").type_kind == TypeKind.KEY
    assert TypeInfo.get_type_name_info("StubDataclassData").type_kind == TypeKind.DATA

    # Invalid cases
    with pytest.raises(Exception):
        # Not a string name
        TypeInfo.get_type_name_info(123)  # noqa
    with pytest.raises(Exception):
        # Not a known type name
        TypeInfo.get_type_name_info("123")  # noqa


def test_from_type_name():
    """Test getting class from type names."""

    assert TypeInfo.from_type_name("TypeDecl") is TypeDecl
    assert TypeInfo.from_type_name("StubDataclass") is StubDataclass
    assert TypeInfo.from_type_name("StubDataclassKey") is StubDataclassKey
    assert TypeInfo.from_type_name("StubDataclassData") is StubDataclassData


def test_import_type():
    """Test importing class using its qualname."""

    # Classes that is already imported
    for imported_class in [TypeInfo, TypeDecl, StubDataclass]:
        assert TypeInfo._import_type(qual_name=qualname(imported_class)) == imported_class

    # Class that is dynamically imported on demand
    do_not_import_qual_name = (
        "stubs.cl.runtime.records.for_dataclasses.stub_dataclass_do_not_import.StubDataclassDoNotImport"
    )
    do_not_import_class = TypeInfo._import_type(qual_name=do_not_import_qual_name)
    assert do_not_import_qual_name == qualname(do_not_import_class)

    # Module does not exist error
    with pytest.raises(RuntimeError):
        qual_name_with_unknown_module = "unknown_module.StubDataclassDoNotImport"
        TypeInfo._import_type(qual_name=qual_name_with_unknown_module)

    # Class does not exist error
    with pytest.raises(RuntimeError):
        qual_name_with_unknown_class = (
            "stubs.cl.runtime.records.for_dataclasses.stub_dataclass_do_not_import.UnknownClass"
        )
        TypeInfo._import_type(qual_name=qual_name_with_unknown_class)


def test_get_types():
    """Test TypeInfo.get_types method."""

    # Included in data types
    data_types = TypeInfo.get_types(type_kind=TypeKind.DATA)
    assert DataMixin in data_types
    assert StubDataclassData in data_types
    # Excluded from data types
    assert KeyMixin not in data_types
    assert RecordMixin not in data_types
    assert _StubDataclassUnderscore not in data_types
    assert __StubDataclassDoubleUnderscore not in data_types

    # Included in record types
    record_types = TypeInfo.get_types(type_kind=TypeKind.RECORD)
    assert RecordMixin in record_types
    assert StubDataclass in record_types
    assert TypeDecl in record_types
    # Excluded from record types
    assert DataMixin not in record_types
    assert KeyMixin not in record_types
    assert StubDataclassKey not in record_types
    assert StubDataclassData not in record_types

    # Included in key types
    key_types = TypeInfo.get_types(type_kind=TypeKind.KEY)
    assert KeyMixin in key_types
    assert StubDataclassKey in key_types
    # Excluded from key types
    assert DataMixin not in key_types
    assert RecordMixin not in key_types
    assert StubDataclassData not in key_types

    # Included in enum types
    enum_types = TypeInfo.get_types(type_kind=TypeKind.ENUM)
    assert StubIntEnum in enum_types
    # Excluded from enum types
    assert Enum not in enum_types  # TODO: Enum base is excluded, review
    assert IntEnum not in enum_types  # TODO: IntEnum base is excluded, review
    assert DataMixin not in enum_types
    assert KeyMixin not in enum_types
    assert RecordMixin not in enum_types


def test_get_parent_and_self_types():
    """Test TypeInfo.get_parent_and_self_types method."""
    assert TypeInfo.get_parent_and_self_types(StubDataclass) == (StubDataclass, StubDataclassKey)
    assert TypeInfo.get_parent_and_self_types(StubDataclass, type_kind=TypeKind.RECORD) == (StubDataclass,)
    assert TypeInfo.get_parent_and_self_types(StubDataclass, type_kind=TypeKind.KEY) == (StubDataclassKey,)
    assert TypeInfo.get_parent_and_self_types(StubDataclassDerived) == (
        StubDataclass,
        StubDataclassDerived,
        StubDataclassKey,
    )


def test_get_child_and_self_types():
    """Test TypeInfo.get_child_and_self_types method."""
    assert TypeInfo.get_child_and_self_types(StubDataclassDerived) == (
        StubDataclassDerived,
        StubDataclassDoubleDerived,
    )
    assert TypeInfo.get_child_and_self_types(StubDataclassPrimitiveFieldsKey, type_kind=TypeKind.RECORD) == (
        StubDataclassPrimitiveFields,
    )
    assert TypeInfo.get_child_and_self_types(StubDataclassPrimitiveFieldsKey, type_kind=TypeKind.KEY) == (
        StubDataclassPrimitiveFieldsKey,
    )
    assert TypeInfo.get_child_and_self_types(StubDataclassPrimitiveFieldsKey) == (
        StubDataclassPrimitiveFields,
        StubDataclassPrimitiveFieldsKey,
    )


def test_get_common_base_type():
    """Test TypeInfo.get_common_base_type method."""
    assert TypeInfo.get_common_base_type([StubDataclass]) is StubDataclass
    assert TypeInfo.get_common_base_type([StubDataclassKey]) is StubDataclassKey
    assert TypeInfo.get_common_base_type([StubDataclass, StubDataclassKey]) is StubDataclassKey
    assert TypeInfo.get_common_base_type([StubDataclass, StubDataclassKey, StubDataclassDerived]) is StubDataclassKey
    assert TypeInfo.get_common_base_type([StubDataclass, StubDataclassDerived]) is StubDataclass
    assert TypeInfo.get_common_base_type([StubDataclassOtherDerived, StubDataclassDerived]) is StubDataclass


if __name__ == "__main__":
    pytest.main([__file__])
