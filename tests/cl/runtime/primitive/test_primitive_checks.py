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
from cl.runtime.records.none_checks import NoneChecks


def test_guard_none():
    """Test for guard_none method."""

    # Valid cases
    assert NoneChecks.guard_none(None)
    assert NoneChecks.guard_none(None, raise_on_fail=False)

    # Invalid cases
    assert not NoneChecks.guard_none(123, raise_on_fail=False)
    with pytest.raises(Exception):
        assert not NoneChecks.guard_none(123)


def test_guard_not_none():
    """Test for guard_not_none method."""

    # Valid cases
    assert NoneChecks.guard_not_none(123)
    assert NoneChecks.guard_not_none(123, raise_on_fail=False)

    # Invalid cases
    assert not NoneChecks.guard_not_none(None, raise_on_fail=False)
    with pytest.raises(Exception):
        assert not NoneChecks.guard_not_none(None)


if __name__ == "__main__":
    pytest.main([__file__])
