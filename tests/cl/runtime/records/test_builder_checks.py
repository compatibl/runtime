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
from cl.runtime.records.builder_checks import BuilderChecks
from stubs.cl.runtime import StubDataclass


def test_guard_frozen():
    """Test BuilderChecks.guard_frozen method."""

    # None
    assert not BuilderChecks.guard_frozen(None, raise_on_fail=False)
    with pytest.raises(Exception, match="does not have build"):
        BuilderChecks.guard_frozen(None)

    # Not a builder
    assert not BuilderChecks.guard_frozen(123, raise_on_fail=False)
    with pytest.raises(Exception, match="does not have build"):
        BuilderChecks.guard_frozen(123)

    # Not frozen
    not_frozen = StubDataclass()
    assert not BuilderChecks.guard_frozen(not_frozen, raise_on_fail=False)
    with pytest.raises(Exception, match="is not frozen"):
        BuilderChecks.guard_frozen(not_frozen)

    # Frozen
    frozen = not_frozen.build()
    assert BuilderChecks.guard_frozen(frozen, raise_on_fail=False)
    assert BuilderChecks.guard_frozen(frozen)


def test_guard_frozen_or_none():
    """Test BuilderChecks.guard_frozen_or_none method."""

    # None
    assert BuilderChecks.guard_frozen_or_none(None, raise_on_fail=False)
    assert BuilderChecks.guard_frozen_or_none(None)

    # Not a builder
    assert not BuilderChecks.guard_frozen_or_none(123, raise_on_fail=False)
    with pytest.raises(Exception, match="does not have build"):
        BuilderChecks.guard_frozen_or_none(123)

    # Not frozen
    not_frozen = StubDataclass()
    assert not BuilderChecks.guard_frozen_or_none(not_frozen, raise_on_fail=False)
    with pytest.raises(Exception, match="is not frozen"):
        BuilderChecks.guard_frozen_or_none(not_frozen)

    # Frozen
    frozen = not_frozen.build()
    assert BuilderChecks.guard_frozen_or_none(frozen, raise_on_fail=False)
    assert BuilderChecks.guard_frozen_or_none(frozen)


if __name__ == "__main__":
    pytest.main([__file__])
