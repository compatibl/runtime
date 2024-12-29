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
from cl.runtime.primitive.format_util import BoolUtil

def _test_format(*, method: Callable, allow_none: bool) -> None:
    """Test the specified callable."""
    if allow_none:
        assert method(None) is None
    else:
        with pytest.raises(Exception):
            method(None)
    assert method(True) == "Y"
    assert method(False) == "N"
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
    assert method("Y")
    assert not method("N")
    with pytest.raises(Exception):
        method("True")
    with pytest.raises(Exception):
        method("True")
    with pytest.raises(Exception):
        method("y")
    with pytest.raises(Exception):
        method("False")
    with pytest.raises(Exception):
        method("false")
    with pytest.raises(Exception):
        method("n")


def test_format():
    """Test for BoolUtil.format."""
    _test_format(method=BoolUtil.format, allow_none=False)


def test_format_or_none():
    """Test for BoolUtil.format_or_none."""
    _test_format(method=BoolUtil.format_or_none, allow_none=True)


def test_parse():
    """Test for BoolUtil.format."""
    _test_parse(method=BoolUtil.parse, allow_none=False)


def test_parse_or_none():
    """Test for BoolUtil.format_or_none."""
    _test_parse(method=BoolUtil.parse_or_none, allow_none=True)


if __name__ == "__main__":
    pytest.main([__file__])
