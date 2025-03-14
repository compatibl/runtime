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
from uuid import UUID
from cl.runtime.primitive.uuid_util import UuidUtil


def test_to_str():
    """Test for UuidUtil.to_str method."""

    assert UuidUtil.to_str(UUID("1a" * 16)) == "1a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a"
    with pytest.raises(Exception):
        assert UuidUtil.to_str(None)  # noqa
    with pytest.raises(Exception):
        assert UuidUtil.to_str("")  # noqa
    with pytest.raises(Exception):
        assert UuidUtil.to_str("null")  # noqa
    with pytest.raises(Exception):
        assert UuidUtil.to_str("None")  # noqa


def test_from_str():
    """Test for UuidUtil.from_str method."""

    assert UuidUtil.from_str("1a1a1a1a-1a1a-1a1a-1a1a-1a1a1a1a1a1a") == UUID("1a" * 16)  # Lowercase
    assert UuidUtil.from_str("1A1A1A1A-1A1A-1A1A-1A1A-1A1A1A1A1A1A") == UUID("1a" * 16)  # Uppercase
    assert UuidUtil.from_str("1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a") == UUID("1a" * 16)  # No delimiters
    with pytest.raises(Exception):
        assert UuidUtil.from_str(None)  # noqa
    with pytest.raises(Exception):
        assert UuidUtil.from_str("")  # noqa
    with pytest.raises(Exception):
        assert UuidUtil.from_str("null")  # noqa
    with pytest.raises(Exception):
        assert UuidUtil.from_str("None")  # noqa


if __name__ == "__main__":
    pytest.main([__file__])
