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
from cl.runtime.records.type_check import TypeCheck
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassKey


def test_is_same_type():
    """Test for is_same_type method."""
    TypeCheck.is_same_type(int, int)
    TypeCheck.is_same_type(StubDataclass, StubDataclass)
    with pytest.raises(Exception):
        TypeCheck.is_same_type(int, float)
    with pytest.raises(Exception):
        TypeCheck.is_same_type(int, StubDataclass)
    with pytest.raises(Exception):
        TypeCheck.is_same_type(StubDataclassDerived, StubDataclass)


def test_is_same_type_or_subtype():
    """Test for test_is_same_type_or_subtype method."""
    TypeCheck.is_same_type_or_subtype(int, int)
    TypeCheck.is_same_type_or_subtype(StubDataclass, StubDataclass)
    TypeCheck.is_same_type_or_subtype(StubDataclassDerived, StubDataclass)
    with pytest.raises(Exception):
        TypeCheck.is_same_type_or_subtype(int, float)
    with pytest.raises(Exception):
        TypeCheck.is_same_type_or_subtype(int, StubDataclass)


def test_is_type_or_name():
    """Test for is_type_or_name method."""
    # Valid types
    TypeCheck.is_type_or_name(int)
    TypeCheck.is_type_or_name(StubDataclass)
    TypeCheck.is_type_or_name(StubDataclassKey)

    # Valid PascalCase strings
    TypeCheck.is_type_or_name("ValidPascalCase")
    TypeCheck.is_type_or_name("AnotherValidPascalCase")
    TypeCheck.is_type_or_name("ValidPascalCaseWithDigits2")

    # Invalid cases
    with pytest.raises(Exception):
        TypeCheck.is_type_or_name("invalid_pascal_case")
    with pytest.raises(Exception):
        TypeCheck.is_type_or_name("Invalid Pascal Case")
    with pytest.raises(Exception):
        TypeCheck.is_type_or_name(123)
    with pytest.raises(Exception):
        TypeCheck.is_type_or_name(["not", "a", "type"])


def test_is_type_or_name_sequence():
    """Test for is_type_or_name_sequence method."""
    # Valid sequences of types
    TypeCheck.is_type_or_name_sequence([int, float, str])
    TypeCheck.is_type_or_name_sequence([StubDataclass, StubDataclassKey])

    # Valid sequences of PascalCase strings
    TypeCheck.is_type_or_name_sequence(["ValidPascalCase", "AnotherValidPascalCase"])
    TypeCheck.is_type_or_name_sequence(["ValidPascalCase", int, "AnotherValidPascalCase"])

    # Invalid cases
    with pytest.raises(Exception):
        TypeCheck.is_type_or_name_sequence("not_a_sequence")
    with pytest.raises(Exception):
        TypeCheck.is_type_or_name_sequence(123)
    with pytest.raises(Exception):
        TypeCheck.is_type_or_name_sequence([int, "invalid_pascal_case"])
    with pytest.raises(Exception):
        TypeCheck.is_type_or_name_sequence([int, "Invalid Pascal Case"])


def test_is_key_type():
    """Test for is_key_type method."""
    TypeCheck.is_key_type(StubDataclassKey)
    with pytest.raises(Exception):
        TypeCheck.is_key_type(StubDataclass)
    with pytest.raises(Exception):
        TypeCheck.is_key_type(int)


def test_is_key_sequence():
    """Test for is_key_sequence method."""
    # Valid key sequences
    TypeCheck.is_key_sequence([StubDataclassKey()])
    TypeCheck.is_key_sequence([StubDataclassKey(), StubDataclassKey()])

    # Invalid cases
    with pytest.raises(Exception):
        TypeCheck.is_key_sequence("not_a_sequence")
    with pytest.raises(Exception):
        TypeCheck.is_key_sequence(123)
    with pytest.raises(Exception):
        TypeCheck.is_key_sequence([StubDataclass()])
    with pytest.raises(Exception):
        TypeCheck.is_key_sequence([StubDataclassKey(), StubDataclass()])


def test_is_record_type():
    """Test for is_record_type method."""
    # Valid record types
    TypeCheck.is_record_type(StubDataclass)
    TypeCheck.is_record_type(StubDataclassDerived)

    # Invalid cases
    with pytest.raises(Exception):
        TypeCheck.is_record_type(int)
    with pytest.raises(Exception):
        TypeCheck.is_record_type(str)
    with pytest.raises(Exception):
        TypeCheck.is_record_type("not_a_type")
    with pytest.raises(Exception):
        TypeCheck.is_record_type(StubDataclassKey)


def test_is_record_sequence():
    """Test for is_record_sequence method."""
    # Valid record sequences
    TypeCheck.is_record_sequence([StubDataclass()])
    TypeCheck.is_record_sequence([StubDataclass(), StubDataclassDerived()])

    # Invalid cases
    with pytest.raises(Exception):
        TypeCheck.is_record_sequence("not_a_sequence")
    with pytest.raises(Exception):
        TypeCheck.is_record_sequence(123)
    with pytest.raises(Exception):
        TypeCheck.is_record_sequence([int])
    with pytest.raises(Exception):
        TypeCheck.is_record_sequence([StubDataclass(), int])
    with pytest.raises(Exception):
        TypeCheck.is_record_sequence([StubDataclassKey()])


def test_is_key_or_record_type():
    """Test for is_key_or_record_type method."""
    # Valid key or record types
    TypeCheck.is_key_or_record_type(StubDataclass)
    TypeCheck.is_key_or_record_type(StubDataclassKey)
    TypeCheck.is_key_or_record_type(StubDataclassDerived)

    # Invalid cases
    with pytest.raises(Exception):
        TypeCheck.is_key_or_record_type(int)
    with pytest.raises(Exception):
        TypeCheck.is_key_or_record_type(str)
    with pytest.raises(Exception):
        TypeCheck.is_key_or_record_type("not_a_type")


def test_is_key_or_record_sequence():
    """Test for is_key_or_record_sequence method."""
    # Valid key or record sequences
    TypeCheck.is_key_or_record_sequence([StubDataclass()])
    TypeCheck.is_key_or_record_sequence([StubDataclassKey()])
    TypeCheck.is_key_or_record_sequence([StubDataclass(), StubDataclassKey()])
    TypeCheck.is_key_or_record_sequence([StubDataclassDerived()])

    # Invalid cases
    with pytest.raises(Exception):
        TypeCheck.is_key_or_record_sequence("not_a_sequence")
    with pytest.raises(Exception):
        TypeCheck.is_key_or_record_sequence(123)
    with pytest.raises(Exception):
        TypeCheck.is_key_or_record_sequence([int])
    with pytest.raises(Exception):
        TypeCheck.is_key_or_record_sequence([StubDataclass(), int])


if __name__ == "__main__":
    pytest.main([__file__])
