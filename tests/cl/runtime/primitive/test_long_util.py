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

from cl.runtime.primitive.limits import check_int_54
from cl.runtime.primitive.long_util import LongUtil


def test_to_str():
    """Test for LongUtil.to_str method."""

    assert LongUtil.to_str(1000) == "1000"
    assert LongUtil.to_str(-1000) == "-1000"
    with pytest.raises(Exception):
        assert LongUtil.to_str(None)  # noqa
    with pytest.raises(Exception):
        assert LongUtil.to_str("")  # noqa
    with pytest.raises(Exception):
        assert LongUtil.to_str("null")  # noqa
    with pytest.raises(Exception):
        assert LongUtil.to_str("None")  # noqa


def test_from_str():
    """Test for LongUtil.from_str method."""

    assert LongUtil.from_str("1000") == 1000
    assert LongUtil.from_str("-1000") == -1000
    with pytest.raises(Exception):
        assert LongUtil.from_str(None)  # noqa
    with pytest.raises(Exception):
        assert LongUtil.from_str("")  # noqa
    with pytest.raises(Exception):
        assert LongUtil.from_str("null")  # noqa
    with pytest.raises(Exception):
        assert LongUtil.from_str("None")  # noqa

def test_int_54():
    """Test for check_int_32 method."""

    check_int_54(1000)
    with pytest.raises(Exception):
        check_int_54("")  # noqa
    with pytest.raises(Exception):
        check_int_54("null")  # noqa
    with pytest.raises(Exception):
        check_int_54("None")  # noqa
    with pytest.raises(Exception):
        check_int_54(2 ** 53)  # Out of int54 range


if __name__ == "__main__":
    pytest.main([__file__])
