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
from stubs.cl.runtime import StubDataclassData
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassKey

_DATA_INSTANCE = StubDataclassData().build()
_DATA_INSTANCE_NOT_FROZEN = StubDataclassData()
_KEY_INSTANCE = StubDataclassKey().build()
_KEY_INSTANCE_NOT_FROZEN = StubDataclassKey()
_RECORD_INSTANCE = StubDataclass().build()
_RECORD_INSTANCE_NOT_FROZEN = StubDataclass()
_DERIVED_RECORD_INSTANCE = StubDataclassDerived().build()


def test_is_key_type():
    """Test for is_key_type method."""

    TypeCheck.guard_key_type(StubDataclassKey)
    # Test that record type is not a key type
    with pytest.raises(Exception):
        TypeCheck.guard_key_type(StubDataclass)
    # Test that data type is not a key type
    with pytest.raises(Exception):
        TypeCheck.guard_key_type(StubDataclassData)
    with pytest.raises(Exception):
        TypeCheck.guard_key_type(int)
    with pytest.raises(Exception):
        # Instance rather than type
        TypeCheck.guard_key_type(_KEY_INSTANCE)


def test_is_key_instance():
    """Test for is_key_instance method."""

    for allow_none in [True, False]:

        method = TypeCheck.guard_key_instance_or_none if allow_none else TypeCheck.guard_key_instance
        if allow_none:
            method(None)
        else:
            with pytest.raises(Exception):
                method(None)

        # Valid cases
        method(_KEY_INSTANCE)

        with pytest.raises(Exception):
            # Not frozen
            method(_KEY_INSTANCE_NOT_FROZEN)
        with pytest.raises(Exception):
            # Test that record instance is not a key instance
            method(_RECORD_INSTANCE)
        with pytest.raises(Exception):
            # Test that data instance is not a key instance
            method(_DATA_INSTANCE)
        with pytest.raises(Exception):
            method(123)
        with pytest.raises(Exception):
            # Instance rather than type
            method(StubDataclassKey)


def test_is_key_sequence():
    """Test for is_key_sequence method."""

    for allow_none in [True, False]:

        method = TypeCheck.guard_key_sequence_or_none if allow_none else TypeCheck.guard_key_sequence
        if allow_none:
            method(None)
        else:
            with pytest.raises(Exception):
                method(None)

        # Valid key sequences
        method([_KEY_INSTANCE])
        method([_KEY_INSTANCE, _KEY_INSTANCE])

        # Invalid cases
        with pytest.raises(Exception):
            # Not frozen
            method([_KEY_INSTANCE_NOT_FROZEN])
        with pytest.raises(Exception):
            method("not_a_sequence")
        with pytest.raises(Exception):
            method(123)
        with pytest.raises(Exception):
            method([_RECORD_INSTANCE])
        with pytest.raises(Exception):
            method([_KEY_INSTANCE, _RECORD_INSTANCE])
        with pytest.raises(Exception):
            # Instance rather than type
            method([_DATA_INSTANCE])
        with pytest.raises(Exception):
            # Instance rather than type
            method([_KEY_INSTANCE, _DATA_INSTANCE])


def test_is_record_type():
    """Test for is_record_type method."""

    # Valid record types
    TypeCheck.guard_record_type(StubDataclass)
    TypeCheck.guard_record_type(StubDataclassDerived)

    # Invalid cases
    with pytest.raises(Exception):
        TypeCheck.guard_record_type(int)
    with pytest.raises(Exception):
        TypeCheck.guard_record_type(str)
    with pytest.raises(Exception):
        TypeCheck.guard_record_type("not_a_type")
    with pytest.raises(Exception):
        TypeCheck.guard_record_type(StubDataclassData)
    with pytest.raises(Exception):
        TypeCheck.guard_record_type(StubDataclassKey)
    with pytest.raises(Exception):
        # Instance rather than type
        TypeCheck.guard_record_type(_RECORD_INSTANCE)


def test_is_record_instance():
    """Test for is_record_instance method."""

    for allow_none in [True, False]:

        method = TypeCheck.guard_record_instance_or_none if allow_none else TypeCheck.guard_record_instance
        if allow_none:
            method(None)
        else:
            with pytest.raises(Exception):
                method(None)

        # Valid record types
        method(_RECORD_INSTANCE)
        method(_DERIVED_RECORD_INSTANCE)

        # Invalid cases
        with pytest.raises(Exception):
            # Not frozen
            method(_RECORD_INSTANCE_NOT_FROZEN)
        with pytest.raises(Exception):
            method(123)
        with pytest.raises(Exception):
            method("abc")
        with pytest.raises(Exception):
            # Type rather than instance
            method(StubDataclass)
        with pytest.raises(Exception):
            # Not a record
            method(_DATA_INSTANCE)
        with pytest.raises(Exception):
            # Not a record
            method(_KEY_INSTANCE)


def test_is_record_sequence():
    """Test for is_record_sequence method."""

    for allow_none in [True, False]:

        method = TypeCheck.guard_record_sequence_or_none if allow_none else TypeCheck.guard_record_sequence
        if allow_none:
            method(None)
        else:
            with pytest.raises(Exception):
                method(None)

        # Valid record sequences
        method([_RECORD_INSTANCE])
        method([_RECORD_INSTANCE, _DERIVED_RECORD_INSTANCE])

        # Invalid cases
        with pytest.raises(Exception):
            method("not_a_sequence")
        with pytest.raises(Exception):
            method(123)
        with pytest.raises(Exception):
            method([int])
        with pytest.raises(Exception):
            method([_RECORD_INSTANCE, int])
        with pytest.raises(Exception):
            method([_KEY_INSTANCE])
        with pytest.raises(Exception):
            # Instance rather than type
            method([_DATA_INSTANCE])
        with pytest.raises(Exception):
            # Instance rather than type
            method([_RECORD_INSTANCE, _DATA_INSTANCE])


def test_is_key_or_record_type():
    """Test for is_key_or_record_type method."""

    # Valid key or record types
    TypeCheck.guard_key_or_record_type(StubDataclass)
    TypeCheck.guard_key_or_record_type(StubDataclassKey)
    TypeCheck.guard_key_or_record_type(StubDataclassDerived)

    # Invalid cases
    with pytest.raises(Exception):
        TypeCheck.guard_key_or_record_type(int)
    with pytest.raises(Exception):
        TypeCheck.guard_key_or_record_type(str)
    with pytest.raises(Exception):
        TypeCheck.guard_key_or_record_type("not_a_type")
    # Test data type (should fail)
    with pytest.raises(Exception):
        # Not a key or record
        TypeCheck.guard_key_or_record_type(StubDataclassData)
    with pytest.raises(Exception):
        # Type rather than instance
        TypeCheck.guard_key_or_record_type(_RECORD_INSTANCE)
    with pytest.raises(Exception):
        # Type rather than instance
        TypeCheck.guard_key_or_record_type(_KEY_INSTANCE)


def test_is_key_or_record_instance():
    """Test for is_key_or_record_instance method."""

    for allow_none in [True, False]:

        method = TypeCheck.guard_key_or_record_instance_or_none if allow_none else TypeCheck.guard_key_or_record_instance
        if allow_none:
            method(None)
        else:
            with pytest.raises(Exception):
                method(None)

        # Valid key or record types
        method(_KEY_INSTANCE)
        method(_RECORD_INSTANCE)
        method(_DERIVED_RECORD_INSTANCE)

        # Invalid cases
        with pytest.raises(Exception):
            # Not frozen
            method(_RECORD_INSTANCE_NOT_FROZEN)
        with pytest.raises(Exception):
            method(123)
        with pytest.raises(Exception):
            method("abc")
        with pytest.raises(Exception):
            # Type rather than instance
            method(StubDataclass)
        with pytest.raises(Exception):
            # Not a key or record
            method(_DATA_INSTANCE)


def test_is_key_or_record_sequence():
    """Test for is_key_or_record_sequence method."""

    for allow_none in [True, False]:

        method = TypeCheck.guard_key_or_record_sequence_or_none if allow_none else TypeCheck.guard_key_or_record_sequence
        if allow_none:
            method(None)
        else:
            with pytest.raises(Exception):
                method(None)

        # Valid key or record sequences
        method([_RECORD_INSTANCE])
        method([_KEY_INSTANCE])
        method([_RECORD_INSTANCE, _KEY_INSTANCE])
        method([_DERIVED_RECORD_INSTANCE])

        # Invalid cases
        with pytest.raises(Exception):
            # Not frozen
            method([_RECORD_INSTANCE_NOT_FROZEN])
        with pytest.raises(Exception):
            method("not_a_sequence")
        with pytest.raises(Exception):
            method(123)
        with pytest.raises(Exception):
            method([int])
        with pytest.raises(Exception):
            method([_RECORD_INSTANCE, int])
        with pytest.raises(Exception):
            # Instance rather than type
            method([_DATA_INSTANCE])
        with pytest.raises(Exception):
            # Instance rather than type
            method([_RECORD_INSTANCE, _DATA_INSTANCE])


if __name__ == "__main__":
    pytest.main([__file__])
