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
from cl.runtime.primitive.int_util import IntUtil


def test_to_str():
    """Test for IntUtil.to_str method."""

    assert IntUtil.to_str(1000) == "1000"
    assert IntUtil.to_str(-1000) == "-1000"
    with pytest.raises(Exception):
        assert IntUtil.to_str(None)  # noqa
    with pytest.raises(Exception):
        assert IntUtil.to_str("")  # noqa
    with pytest.raises(Exception):
        assert IntUtil.to_str("null")  # noqa
    with pytest.raises(Exception):
        assert IntUtil.to_str("None")  # noqa
    with pytest.raises(Exception):
        assert IntUtil.to_str(2 ** 31) # Out of int32 range


def test_from_str():
    """Test for IntUtil.from_str method."""

    assert IntUtil.from_str("1000") == 1000
    assert IntUtil.from_str("-1000") == -1000
    with pytest.raises(Exception):
        assert IntUtil.from_str(None)  # noqa
    with pytest.raises(Exception):
        assert IntUtil.from_str("")  # noqa
    with pytest.raises(Exception):
        assert IntUtil.from_str("null")  # noqa
    with pytest.raises(Exception):
        assert IntUtil.from_str("None")  # noqa
    with pytest.raises(Exception):
        assert IntUtil.from_str("2147483648") # Out of int32 range


def test_check_range():
    """Test for IntUtil.check_range method."""

    IntUtil.check_range(1000)
    with pytest.raises(Exception):
        IntUtil.check_range(None)  # noqa
    with pytest.raises(Exception):
        IntUtil.check_range("")  # noqa
    with pytest.raises(Exception):
        IntUtil.check_range("null")  # noqa
    with pytest.raises(Exception):
        IntUtil.check_range("None")  # noqa
    with pytest.raises(Exception):
        IntUtil.check_range(2 ** 31) # Out of int32 range


if __name__ == "__main__":
    pytest.main([__file__])
