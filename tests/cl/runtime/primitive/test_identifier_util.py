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
from cl.runtime.primitive.identifier_util import IdentifierUtil


def test_guard_valid_identifier():
    """Test for 'guard_valid_identifier' method."""

    # Valid cases
    IdentifierUtil.guard_valid_identifier("abc")  # Allow identifier without delimiter
    IdentifierUtil.guard_valid_identifier("abc.xyz")  # Allow identifier with delimiter

    # Invalid cases
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc|xyz")
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc(xyz")
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc)xyz")
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc\\xyz")
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc/xyz")
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc{xyz")
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc}xyz")

    # Test with raise_on_fail = False
    assert not IdentifierUtil.guard_valid_identifier("abc|xyz", raise_on_fail=False)


def test_guard_valid_directory():
    """Test for 'check_valid_path' method."""

    # Valid cases
    IdentifierUtil.guard_valid_identifier("abc", allow_directory_separators=True)  # Allow path without delimiter
    IdentifierUtil.guard_valid_identifier("abc.xyz", allow_directory_separators=True)  # Allow path with delimiter
    IdentifierUtil.guard_valid_identifier("mydir\\mydir\\abc.xyz", allow_directory_separators=True)
    IdentifierUtil.guard_valid_identifier("mydir/mydir/abc.xyz", allow_directory_separators=True)

    # Invalid cases
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc(xyz", allow_directory_separators=True)
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc)xyz", allow_directory_separators=True)
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc|xyz", allow_directory_separators=True)
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("mydir\\mydir\\abc[xyz", allow_directory_separators=True)
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc{xyz", allow_directory_separators=True)
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc}xyz", allow_directory_separators=True)

    # Test with raise_on_fail = False
    assert not IdentifierUtil.guard_valid_identifier("abc|xyz", allow_directory_separators=True, raise_on_fail=False)


def test_guard_valid_format():
    """Test for 'guard_valid_identifier' method."""

    # Valid cases
    IdentifierUtil.guard_valid_identifier("abc", allow_braces=True)  # Allow identifier without delimiter
    IdentifierUtil.guard_valid_identifier("abc.xyz", allow_braces=True)  # Allow identifier with delimiter
    IdentifierUtil.guard_valid_identifier("abc{xyz", allow_braces=True)
    IdentifierUtil.guard_valid_identifier("abc}xyz", allow_braces=True)

    # Invalid cases
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc|xyz", allow_braces=True)
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc(xyz", allow_braces=True)
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc)xyz", allow_braces=True)
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc\\xyz", allow_braces=True)
    with pytest.raises(RuntimeError):
        IdentifierUtil.guard_valid_identifier("abc/xyz", allow_braces=True)

    # Test with raise_on_fail = False
    assert not IdentifierUtil.guard_valid_identifier("abc|xyz", allow_braces=True, raise_on_fail=False)


if __name__ == "__main__":
    pytest.main([__file__])
