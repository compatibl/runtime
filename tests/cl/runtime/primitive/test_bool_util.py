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
from typing import Callable
from cl.runtime.primitive.bool_util import BoolUtil


def _test_format(*, method: Callable, allow_none: bool) -> None:
    """Test the specified callable."""
    if allow_none:
        assert method(None) is None
    else:
        with pytest.raises(Exception):
            method(None)
    assert method(True) == "true"
    assert method(False) == "false"
    with pytest.raises(Exception):
        # Another type
        method(0)


def _test_parse(*, method: Callable, allow_none: bool) -> None:
    """Test the specified callable."""
    if allow_none:
        assert method(None) is None
    else:
        with pytest.raises(Exception):
            method(None)
    assert method("true")
    assert not method("false")
    with pytest.raises(Exception):
        method("True")
    with pytest.raises(Exception):
        method("Y")
    with pytest.raises(Exception):
        method("y")
    with pytest.raises(Exception):
        method("False")
    with pytest.raises(Exception):
        method("N")
    with pytest.raises(Exception):
        method("n")


def test_format():
    """Test for BoolUtil.format."""
    _test_format(method=BoolUtil.to_str, allow_none=False)


def test_serialize():
    """Test for BoolUtil.serialize."""
    _test_format(method=BoolUtil.to_str_or_none, allow_none=True)


def test_parse():
    """Test for BoolUtil.format."""
    _test_parse(method=BoolUtil.from_str, allow_none=False)


def test_parse_or_none():
    """Test for BoolUtil.serialize."""
    _test_parse(method=BoolUtil.from_str_or_none, allow_none=True)


def test_roundtrip():
    """Test roundtrip serialization and deserialization."""

    test_cases = [
        ("bool", None, None, "", "null"),
        ("bool", True, "true"),
        ("bool", False, "false"),
    ]

    for test_case in test_cases:

        # Get type_name, value, expected serialized value, and an optional list of alternative serialized values
        type_name, value, serialized, *alternative_serialized_list = test_case

        # Test roundtrip serialization and deserialization
        if value is not None:
            assert BoolUtil.to_str(value) == serialized
            assert BoolUtil.from_str(serialized) == value
        assert BoolUtil.to_str_or_none(value) == serialized
        assert BoolUtil.from_str_or_none(serialized) == value

        # Test alternative serialized forms
        if alternative_serialized_list:
            for alternative_serialized in alternative_serialized_list:
                if value is not None:
                    assert BoolUtil.from_str(alternative_serialized) == value
                assert BoolUtil.from_str_or_none(alternative_serialized) == value


def test_serialization_exceptions():
    """Test roundtrip serialization and deserialization."""

    test_cases = [
        ("bool", None),
        ("bool", 0),
        ("bool", "None"),
        ("bool", "Null"),
    ]

    # Check exception cases
    for test_case in test_cases:
        type_name, value = test_case
        with pytest.raises(Exception):
            BoolUtil.to_str(value)
        if value is not None:
            with pytest.raises(Exception):
                BoolUtil.to_str_or_none(value)


def test_deserialization_exceptions():
    """Test roundtrip serialization and deserialization."""

    test_cases = [
        ("bool", None),  # Allowed for from_str_or_none
        ("bool", ""),  # Allowed for from_str_or_none
        ("bool", "null"),  # Allowed for from_str_or_none
        ("bool", 0),
        ("bool", "None"),
        ("bool", "Null"),
        ("bool", "True"),
        ("bool", "False"),
        ("bool", "Y"),
        ("bool", "N"),
        ("bool", "YES"),
        ("bool", "NO"),  # Norway problem
    ]

    # Check exception cases
    for test_case in test_cases:
        type_name, serialized = test_case
        with pytest.raises(Exception):
            BoolUtil.from_str(serialized)
        if serialized not in BoolUtil.NONE_VALUES:
            with pytest.raises(Exception):
                BoolUtil.from_str_or_none(serialized)


if __name__ == "__main__":
    pytest.main([__file__])
