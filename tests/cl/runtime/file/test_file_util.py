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
from cl.runtime.file.file_util import FileUtil


def test_check_valid_filename():
    """Test for 'check_valid_filename' method."""
    FileUtil.guard_valid_filename("abc")  # Allow filenames without extension
    FileUtil.guard_valid_filename("abc.xyz")
    with pytest.raises(RuntimeError):
        FileUtil.guard_valid_filename("abc|xyz")
    with pytest.raises(RuntimeError):
        FileUtil.guard_valid_filename("abc\\xyz")
    with pytest.raises(RuntimeError):
        FileUtil.guard_valid_filename("abc/xyz")


def test_check_valid_path():
    """Test for 'check_valid_path' method."""
    FileUtil.guard_valid_path("abc")  # Allow filenames without extension
    FileUtil.guard_valid_path("abc.xyz")  # Allow filenames with no path
    FileUtil.guard_valid_path("mydir\\mydir\\abc.xyz")
    FileUtil.guard_valid_path("mydir/mydir/abc.xyz")
    with pytest.raises(RuntimeError):
        FileUtil.guard_valid_path("abc|xyz")
    # TODO: fix
    # with pytest.raises(RuntimeError):
    #     FileUtil.guard_valid_path("mydir\\mydir\\abc[xyz")


def test_has_extension():
    """Test for 'has_extension' method."""

    # Check for any extension
    assert FileUtil.has_extension("abc", None)
    assert not FileUtil.has_extension("abc.xyz", None)

    # Check for a specific extension
    assert FileUtil.has_extension("abc.xyz", "xyz")
    assert not FileUtil.has_extension("abc", "xyz")
    assert not FileUtil.has_extension("abc.xyz", "abc")


def test_check_extension():
    """Test for 'check_extension' method."""

    # Check for any extension
    FileUtil.check_extension("abc", None)
    with pytest.raises(RuntimeError):
        FileUtil.check_extension("abc.xyz", None)

    # Check for a specific extension
    FileUtil.check_extension("abc.xyz", "xyz")
    with pytest.raises(RuntimeError):
        FileUtil.check_extension("abc", "xyz")
    with pytest.raises(RuntimeError):
        FileUtil.check_extension("abc.xyz", "abc")


def test_normalize_ext():
    """Test for 'normalize_ext' method."""

    # Test with None
    assert FileUtil.normalize_ext(None) is None

    # Test with empty string
    assert FileUtil.normalize_ext("") is None

    # Test with extension with leading dot
    assert FileUtil.normalize_ext(".json") == "json"
    assert FileUtil.normalize_ext(".CSV") == "csv"

    # Test with extension without leading dot
    assert FileUtil.normalize_ext("json") == "json"
    assert FileUtil.normalize_ext("CSV") == "csv"

    # Test case conversion
    assert FileUtil.normalize_ext(".TXT") == "txt"
    assert FileUtil.normalize_ext("XML") == "xml"


def test_get_type_from_filename():
    """Test for 'get_type_from_filename' method."""

    # Test with valid type in PascalCase
    result = FileUtil.get_type_from_filename("StubDataclass.json")
    assert result is not None

    # Test with invalid PascalCase and error=True (should raise)
    with pytest.raises(RuntimeError, match="is not a valid type"):
        FileUtil.get_type_from_filename("invalid_name.json")

    with pytest.raises(RuntimeError, match="is not a valid type"):
        FileUtil.get_type_from_filename("lowercase.json")

    # Test with invalid PascalCase and error=False (should return None, not raise)
    result = FileUtil.get_type_from_filename("invalid_name.json", raise_on_fail=False)
    assert result is None

    result = FileUtil.get_type_from_filename("lowercase.json", raise_on_fail=False)
    assert result is None

    # Test with valid PascalCase but non-existent type and error=True (should raise)
    with pytest.raises(RuntimeError, match="is not a valid type"):
        FileUtil.get_type_from_filename("NonExistentType.json")

    # Test with valid PascalCase but non-existent type and error=False (should return None)
    result = FileUtil.get_type_from_filename("NonExistentType.json", raise_on_fail=False)
    assert result is None

    # Test with path containing invalid PascalCase
    with pytest.raises(RuntimeError, match="is not a valid type"):
        FileUtil.get_type_from_filename("/path/to/invalid_name.json")

    # Test with path and error=False
    result = FileUtil.get_type_from_filename("/path/to/invalid_name.json", raise_on_fail=False)
    assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
